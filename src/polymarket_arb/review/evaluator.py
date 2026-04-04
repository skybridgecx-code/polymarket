from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from polymarket_arb.models.review import ReplayEvaluation, ReviewPacket, canonical_json


class ReplayEvaluationService:
    def evaluate_packet_paths(
        self,
        *,
        baseline_path: str,
        candidate_path: str,
    ) -> dict[str, Any]:
        baseline_packet = ReviewPacket.model_validate(
            json.loads(Path(baseline_path).read_text(encoding="utf-8"))
        )
        candidate_packet = ReviewPacket.model_validate(
            json.loads(Path(candidate_path).read_text(encoding="utf-8"))
        )
        return self.evaluate_packets(
            baseline_packet=baseline_packet,
            candidate_packet=candidate_packet,
        ).to_output()

    def evaluate_packets(
        self,
        *,
        baseline_packet: ReviewPacket,
        candidate_packet: ReviewPacket,
    ) -> ReplayEvaluation:
        evaluation_id = self._evaluation_id(
            baseline_packet_id=baseline_packet.packet_id,
            candidate_packet_id=candidate_packet.packet_id,
        )

        if baseline_packet.packet_type != candidate_packet.packet_type:
            return ReplayEvaluation(
                evaluation_id=evaluation_id,
                subject_type=baseline_packet.packet_type,
                compared_records_count=0,
                matches_count=0,
                mismatches_count=0,
                drift_reasons=[
                    f"packet_type_mismatch:{baseline_packet.packet_type}:{candidate_packet.packet_type}"
                ],
                status="fail",
                explanation="Failed because the packets do not describe the same subject type.",
            )

        baseline_records = dict(
            zip(
                baseline_packet.raw_result_references,
                baseline_packet.embedded_records,
                strict=True,
            )
        )
        candidate_records = dict(
            zip(
                candidate_packet.raw_result_references,
                candidate_packet.embedded_records,
                strict=True,
            )
        )

        compared_references = sorted(set(baseline_records) | set(candidate_records))
        matches_count = 0
        mismatches_count = 0
        drift_reasons: list[str] = []

        for reference in compared_references:
            baseline_record = baseline_records.get(reference)
            candidate_record = candidate_records.get(reference)
            if baseline_record is None:
                mismatches_count += 1
                drift_reasons.append(f"missing_in_baseline:{reference}")
                continue
            if candidate_record is None:
                mismatches_count += 1
                drift_reasons.append(f"missing_in_candidate:{reference}")
                continue
            if canonical_json(baseline_record) == canonical_json(candidate_record):
                matches_count += 1
                continue

            mismatches_count += 1
            for field in self._field_drift_reasons(
                reference=reference,
                baseline_record=baseline_record,
                candidate_record=candidate_record,
            ):
                drift_reasons.append(field)

        status: Literal["pass", "fail"] = "pass" if mismatches_count == 0 else "fail"
        explanation = (
            f"Compared {len(compared_references)} records for {baseline_packet.packet_type}; "
            f"{matches_count} matched and {mismatches_count} drifted."
        )

        return ReplayEvaluation(
            evaluation_id=evaluation_id,
            subject_type=baseline_packet.packet_type,
            compared_records_count=len(compared_references),
            matches_count=matches_count,
            mismatches_count=mismatches_count,
            drift_reasons=drift_reasons,
            status=status,
            explanation=explanation,
        )

    def _field_drift_reasons(
        self,
        *,
        reference: str,
        baseline_record: dict[str, Any],
        candidate_record: dict[str, Any],
    ) -> list[str]:
        fields = sorted(set(baseline_record) | set(candidate_record))
        reasons: list[str] = []
        for field in fields:
            if baseline_record.get(field) != candidate_record.get(field):
                reasons.append(f"field_mismatch:{reference}:{field}")
        return reasons

    def _evaluation_id(self, *, baseline_packet_id: str, candidate_packet_id: str) -> str:
        digest = hashlib.sha256(
            canonical_json(
                {
                    "baseline_packet_id": baseline_packet_id,
                    "candidate_packet_id": candidate_packet_id,
                }
            ).encode("utf-8")
        ).hexdigest()[:16]
        return f"evaluation:{digest}"
