"""Bounded live analyst adapter and transport boundary for runtime integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

import httpx

from future_system.live_analyst.errors import (
    LiveAnalystTimeoutError,
    LiveAnalystTransportError,
)
from future_system.live_analyst.models import LiveAnalystTransportRequest
from future_system.reasoning_contracts.models import ReasoningInputPacket, RenderedPromptPacket
from future_system.runtime.protocol import AnalystProtocol, AnalystResponsePayload


@runtime_checkable
class LiveAnalystTransportProtocol(Protocol):
    """Transport protocol for one bounded model-call request/response cycle."""

    def request(
        self,
        *,
        request: LiveAnalystTransportRequest,
    ) -> Mapping[str, Any] | str:
        """Execute a bounded model-call request and return transport response payload."""


class HttpxLiveAnalystTransport(LiveAnalystTransportProtocol):
    """Small HTTP transport boundary for live analyst requests."""

    def __init__(
        self,
        *,
        endpoint_url: str,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        normalized_endpoint = endpoint_url.strip()
        if not normalized_endpoint:
            raise ValueError("endpoint_url must be a non-empty string.")

        self._endpoint_url = normalized_endpoint
        self._api_key = api_key.strip() if api_key is not None else None
        self._client = client or httpx.Client()

    def request(
        self,
        *,
        request: LiveAnalystTransportRequest,
    ) -> Mapping[str, Any]:
        headers = {"content-type": "application/json"}
        if self._api_key is not None:
            headers["authorization"] = f"Bearer {self._api_key}"

        try:
            response = self._client.post(
                self._endpoint_url,
                headers=headers,
                json=request.model_dump(mode="json"),
                timeout=request.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise LiveAnalystTimeoutError(
                "live_analyst_timeout: "
                f"endpoint={self._endpoint_url!r}; "
                f"timeout_seconds={request.timeout_seconds:.3f}."
            ) from exc
        except httpx.HTTPError as exc:
            raise LiveAnalystTransportError(
                "live_analyst_transport_failed: "
                f"endpoint={self._endpoint_url!r}; "
                "request did not complete successfully."
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise LiveAnalystTransportError(
                "live_analyst_transport_invalid_response: response body must be JSON."
            ) from exc

        if not isinstance(payload, Mapping):
            raise LiveAnalystTransportError(
                "live_analyst_transport_invalid_response: response JSON must be an object."
            )

        return dict(payload)


class LiveAnalystAdapter(AnalystProtocol):
    """Runtime-compatible analyst adapter backed by a bounded transport boundary."""

    is_stub: bool = False

    def __init__(
        self,
        *,
        transport: LiveAnalystTransportProtocol,
        timeout_seconds: float = 15.0,
        model: str | None = None,
    ) -> None:
        if timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be greater than 0.")

        self._transport = transport
        self._timeout_seconds = float(timeout_seconds)
        self._model = model.strip() if model is not None else None

    def analyze(
        self,
        *,
        reasoning_input: ReasoningInputPacket,
        rendered_prompt: RenderedPromptPacket,
    ) -> AnalystResponsePayload:
        return self.analyze_request(
            reasoning_input=reasoning_input,
            rendered_prompt=rendered_prompt,
        )

    def analyze_request(
        self,
        *,
        reasoning_input: ReasoningInputPacket | None = None,
        rendered_prompt: RenderedPromptPacket | str | None = None,
    ) -> AnalystResponsePayload:
        request = _build_transport_request(
            reasoning_input=reasoning_input,
            rendered_prompt=rendered_prompt,
            timeout_seconds=self._timeout_seconds,
            model=self._model,
        )

        raw_response = self._request_transport(request=request)
        return _extract_content_payload(raw_response)

    def _request_transport(
        self,
        *,
        request: LiveAnalystTransportRequest,
    ) -> Mapping[str, Any] | str:
        try:
            return self._transport.request(request=request)
        except LiveAnalystTimeoutError:
            raise
        except TimeoutError as exc:
            raise LiveAnalystTimeoutError(
                "live_analyst_timeout: "
                f"timeout_seconds={self._timeout_seconds:.3f}."
            ) from exc
        except LiveAnalystTransportError:
            raise
        except Exception as exc:
            raise LiveAnalystTransportError(
                "live_analyst_transport_failed: transport request raised an unexpected error."
            ) from exc


def _build_transport_request(
    *,
    reasoning_input: ReasoningInputPacket | None,
    rendered_prompt: RenderedPromptPacket | str | None,
    timeout_seconds: float,
    model: str | None,
) -> LiveAnalystTransportRequest:
    metadata: dict[str, str] = {}
    if reasoning_input is not None:
        metadata["theme_id"] = reasoning_input.theme_id
        metadata["prompt_version"] = reasoning_input.prompt_version

    if isinstance(rendered_prompt, RenderedPromptPacket):
        payload: dict[str, object] = {
            "system_prompt": rendered_prompt.system_prompt,
            "user_prompt": rendered_prompt.user_prompt,
            "rendered_json_schema": rendered_prompt.rendered_json_schema,
        }
        return LiveAnalystTransportRequest(
            input_mode="rendered_prompt",
            payload=payload,
            timeout_seconds=timeout_seconds,
            model=model,
            metadata=metadata,
        )

    if isinstance(rendered_prompt, str):
        normalized_prompt = rendered_prompt.strip()
        if not normalized_prompt:
            raise ValueError("rendered_prompt must be a non-empty string.")

        return LiveAnalystTransportRequest(
            input_mode="rendered_prompt_text",
            payload={"prompt": normalized_prompt},
            timeout_seconds=timeout_seconds,
            model=model,
            metadata=metadata,
        )

    if reasoning_input is not None:
        return LiveAnalystTransportRequest(
            input_mode="reasoning_input",
            payload=reasoning_input.model_dump(mode="json"),
            timeout_seconds=timeout_seconds,
            model=model,
            metadata=metadata,
        )

    raise ValueError("Live analyst requires reasoning_input or rendered_prompt.")


def _extract_content_payload(response: Mapping[str, Any] | str) -> AnalystResponsePayload:
    if isinstance(response, str):
        normalized = response.strip()
        if not normalized:
            raise LiveAnalystTransportError(
                "live_analyst_transport_invalid_response: response string cannot be empty."
            )
        return normalized

    if "content" in response:
        return _normalize_response_content(response["content"])
    if "output_text" in response:
        return _normalize_response_content(response["output_text"])
    if "choices" in response:
        return _extract_content_from_choices(response["choices"])

    raise LiveAnalystTransportError(
        "live_analyst_transport_invalid_response: missing content/output_text/choices."
    )


def _extract_content_from_choices(choices: Any) -> AnalystResponsePayload:
    if not isinstance(choices, list) or not choices:
        raise LiveAnalystTransportError(
            "live_analyst_transport_invalid_response: choices must be a non-empty list."
        )

    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise LiveAnalystTransportError(
            "live_analyst_transport_invalid_response: choices items must be objects."
        )

    if "message" in first_choice and isinstance(first_choice["message"], Mapping):
        message = first_choice["message"]
        if "content" in message:
            return _normalize_response_content(message["content"])

    if "text" in first_choice:
        return _normalize_response_content(first_choice["text"])

    raise LiveAnalystTransportError(
        "live_analyst_transport_invalid_response: choices item missing message/content."
    )


def _normalize_response_content(content: Any) -> AnalystResponsePayload:
    if isinstance(content, str):
        normalized = content.strip()
        if not normalized:
            raise LiveAnalystTransportError(
                "live_analyst_transport_invalid_response: content string cannot be empty."
            )
        return normalized

    if isinstance(content, Mapping):
        return dict(content)

    raise LiveAnalystTransportError(
        "live_analyst_transport_invalid_response: content must be string or object."
    )
