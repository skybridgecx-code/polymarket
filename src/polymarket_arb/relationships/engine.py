from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from polymarket_arb.models.normalized import NormalizedWalletActivity
from polymarket_arb.models.relationship import RelationshipEvidenceItem, RelationshipReport

_LAG_WINDOW_SECONDS = 300
_MIN_MATCHED_EVENTS = 2
_MIN_MATCHED_LEGS = 3
_MAX_EVIDENCE_ITEMS = 5
_CONFIDENCE_PRECISION = Decimal("0.01")


@dataclass(frozen=True)
class _MatchCandidate:
    leader_wallet: str
    follower_wallet: str
    leader_activity: NormalizedWalletActivity
    follower_activity: NormalizedWalletActivity
    lag_seconds: int

    @property
    def event_slug(self) -> str | None:
        return self.leader_activity.event_slug or self.follower_activity.event_slug

    @property
    def condition_id(self) -> str:
        assert self.leader_activity.condition_id is not None
        return self.leader_activity.condition_id

    @property
    def token_id(self) -> str:
        assert self.leader_activity.token_id is not None
        return self.leader_activity.token_id

    @property
    def side(self) -> str:
        assert self.leader_activity.side is not None
        return self.leader_activity.side


class RelationshipEngine:
    def build_relationship_reports(
        self,
        *,
        activities: list[NormalizedWalletActivity],
    ) -> list[RelationshipReport]:
        eligible_activities = [activity for activity in activities if self._is_eligible(activity)]
        eligible_activities.sort(key=self._activity_sort_key)

        activities_by_wallet: dict[str, list[NormalizedWalletActivity]] = defaultdict(list)
        for activity in eligible_activities:
            activities_by_wallet[activity.wallet_address].append(activity)

        shared_keys_by_wallet = self._shared_keys_by_wallet(eligible_activities)
        reports: list[RelationshipReport] = []

        wallets = sorted(activities_by_wallet)
        for leader_wallet in wallets:
            for follower_wallet in wallets:
                if leader_wallet == follower_wallet:
                    continue
                if not self._shares_any_key(
                    leader_wallet=leader_wallet,
                    follower_wallet=follower_wallet,
                    shared_keys_by_wallet=shared_keys_by_wallet,
                ):
                    continue

                matches = self._build_pair_matches(
                    leader_activities=activities_by_wallet[leader_wallet],
                    follower_activities=activities_by_wallet[follower_wallet],
                )
                reports.append(
                    self._report_from_matches(
                        leader_wallet=leader_wallet,
                        follower_wallet=follower_wallet,
                        matches=matches,
                    )
                )

        reports = self._apply_bidirectional_guard(reports)
        reports.sort(key=self._report_sort_key)
        return reports

    def _build_pair_matches(
        self,
        *,
        leader_activities: list[NormalizedWalletActivity],
        follower_activities: list[NormalizedWalletActivity],
    ) -> list[_MatchCandidate]:
        follower_by_leg: dict[
            tuple[str, str, str],
            list[NormalizedWalletActivity],
        ] = defaultdict(list)
        for activity in follower_activities:
            follower_by_leg[self._leg_key(activity)].append(activity)

        for leg_activities in follower_by_leg.values():
            leg_activities.sort(key=self._activity_sort_key)

        matches: list[_MatchCandidate] = []
        used_follower_ids: set[str] = set()

        for leader_activity in leader_activities:
            leg_key = self._leg_key(leader_activity)
            for follower_activity in follower_by_leg.get(leg_key, []):
                if follower_activity.source_record_id in used_follower_ids:
                    continue
                lag_seconds = self._lag_seconds(leader_activity, follower_activity)
                if lag_seconds is None:
                    continue
                used_follower_ids.add(follower_activity.source_record_id)
                matches.append(
                    _MatchCandidate(
                        leader_wallet=leader_activity.wallet_address,
                        follower_wallet=follower_activity.wallet_address,
                        leader_activity=leader_activity,
                        follower_activity=follower_activity,
                        lag_seconds=lag_seconds,
                    )
                )
                break

        matches.sort(
            key=lambda match: (
                match.event_slug or "",
                match.condition_id,
                match.token_id,
                match.leader_activity.activity_at,
                match.follower_activity.activity_at,
                match.leader_activity.source_record_id,
            )
        )
        return matches

    def _report_from_matches(
        self,
        *,
        leader_wallet: str,
        follower_wallet: str,
        matches: list[_MatchCandidate],
    ) -> RelationshipReport:
        if not matches:
            return self._rejected_report(
                leader_wallet=leader_wallet,
                follower_wallet=follower_wallet,
                rejection_reason="no_same_leg_matches",
                explanation=(
                    "Rejected because the wallets never traded the same condition, "
                    "token, and side within the bounded lag window."
                ),
                matches=[],
            )

        matched_event_slugs = sorted({match.event_slug or match.condition_id for match in matches})
        matched_event_count = len(matched_event_slugs)
        matched_leg_count = len(matches)

        if matched_event_count < _MIN_MATCHED_EVENTS:
            return self._rejected_report(
                leader_wallet=leader_wallet,
                follower_wallet=follower_wallet,
                rejection_reason="insufficient_repeated_events",
                explanation=(
                    "Rejected because the overlap does not repeat across enough distinct events "
                    "to support a copier relationship."
                ),
                matches=matches,
            )

        if matched_leg_count < _MIN_MATCHED_LEGS:
            return self._rejected_report(
                leader_wallet=leader_wallet,
                follower_wallet=follower_wallet,
                rejection_reason="insufficient_match_count",
                explanation=(
                    "Rejected because the pair has too few matched same-leg actions "
                    "after lag-window filtering."
                ),
                matches=matches,
            )

        confidence_score = self._confidence_score(matches)
        lag_summary = self._lag_summary(matches)
        explanation = (
            f"Accepted because {follower_wallet} repeatedly followed {leader_wallet} "
            f"on {matched_leg_count} same-leg trades across {matched_event_count} events "
            f"with median lag {lag_summary['median']} seconds."
        )

        return RelationshipReport(
            leader_wallet=leader_wallet,
            follower_wallet=follower_wallet,
            relationship_type="same_leg_same_side_lag",
            matched_events_count=matched_event_count,
            matched_legs_count=matched_leg_count,
            lag_summary_seconds=lag_summary,
            confidence_score=confidence_score,
            status="accepted",
            rejection_reason=None,
            explanation=explanation,
            evidence=self._evidence(matches),
        )

    def _rejected_report(
        self,
        *,
        leader_wallet: str,
        follower_wallet: str,
        rejection_reason: str,
        explanation: str,
        matches: list[_MatchCandidate],
    ) -> RelationshipReport:
        return RelationshipReport(
            leader_wallet=leader_wallet,
            follower_wallet=follower_wallet,
            relationship_type="same_leg_same_side_lag",
            matched_events_count=len({match.event_slug or match.condition_id for match in matches}),
            matched_legs_count=len(matches),
            lag_summary_seconds=self._lag_summary(matches),
            confidence_score=self._confidence_score(matches) if matches else Decimal("0"),
            status="rejected",
            rejection_reason=rejection_reason,
            explanation=explanation,
            evidence=self._evidence(matches),
        )

    def _apply_bidirectional_guard(
        self,
        reports: list[RelationshipReport],
    ) -> list[RelationshipReport]:
        by_pair = {
            (report.leader_wallet, report.follower_wallet): report
            for report in reports
        }

        for report in reports:
            if report.status != "accepted":
                continue

            reciprocal = by_pair.get((report.follower_wallet, report.leader_wallet))
            if reciprocal is None or reciprocal.status != "accepted":
                continue

            report.status = "rejected"
            report.rejection_reason = "ambiguous_bidirectional_overlap"
            report.explanation = (
                "Rejected because the same bounded-window evidence supports both leader/follower "
                "directions, which is ambiguous."
            )
            reciprocal.status = "rejected"
            reciprocal.rejection_reason = "ambiguous_bidirectional_overlap"
            reciprocal.explanation = report.explanation

        return reports

    def _is_eligible(self, activity: NormalizedWalletActivity) -> bool:
        return (
            activity.activity_type == "TRADE"
            and activity.activity_at is not None
            and activity.condition_id is not None
            and activity.token_id is not None
            and activity.side is not None
        )

    def _shared_keys_by_wallet(
        self,
        activities: list[NormalizedWalletActivity],
    ) -> dict[str, set[tuple[str, str, str]]]:
        shared: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
        for activity in activities:
            shared[activity.wallet_address].add(self._leg_key(activity))
        return shared

    def _shares_any_key(
        self,
        *,
        leader_wallet: str,
        follower_wallet: str,
        shared_keys_by_wallet: dict[str, set[tuple[str, str, str]]],
    ) -> bool:
        return bool(
            shared_keys_by_wallet.get(leader_wallet, set())
            & shared_keys_by_wallet.get(follower_wallet, set())
        )

    def _leg_key(self, activity: NormalizedWalletActivity) -> tuple[str, str, str]:
        assert activity.condition_id is not None
        assert activity.token_id is not None
        assert activity.side is not None
        return (activity.condition_id, activity.token_id, activity.side)

    def _lag_seconds(
        self,
        leader_activity: NormalizedWalletActivity,
        follower_activity: NormalizedWalletActivity,
    ) -> int | None:
        assert leader_activity.activity_at is not None
        assert follower_activity.activity_at is not None
        lag_seconds = int(
            (follower_activity.activity_at - leader_activity.activity_at).total_seconds()
        )
        if lag_seconds <= 0 or lag_seconds > _LAG_WINDOW_SECONDS:
            return None
        return lag_seconds

    def _lag_summary(self, matches: list[_MatchCandidate]) -> dict[str, int | None]:
        if not matches:
            return {"min": None, "median": None, "max": None}

        lags = sorted(match.lag_seconds for match in matches)
        median = lags[len(lags) // 2]
        if len(lags) % 2 == 0:
            median = (lags[(len(lags) // 2) - 1] + lags[len(lags) // 2]) // 2
        return {"min": lags[0], "median": median, "max": lags[-1]}

    def _confidence_score(self, matches: list[_MatchCandidate]) -> Decimal:
        if not matches:
            return Decimal("0")

        matched_event_count = len({match.event_slug or match.condition_id for match in matches})
        matched_leg_count = len(matches)
        median_lag = self._lag_summary(matches)["median"] or _LAG_WINDOW_SECONDS

        event_component = min(Decimal(matched_event_count) / Decimal("4"), Decimal("1"))
        leg_component = min(Decimal(matched_leg_count) / Decimal("5"), Decimal("1"))
        lag_component = Decimal(_LAG_WINDOW_SECONDS - median_lag) / Decimal(_LAG_WINDOW_SECONDS)

        score = (
            (event_component * Decimal("0.45"))
            + (leg_component * Decimal("0.35"))
            + (lag_component * Decimal("0.20"))
        )
        return score.quantize(_CONFIDENCE_PRECISION, rounding=ROUND_HALF_UP)

    def _evidence(self, matches: list[_MatchCandidate]) -> list[RelationshipEvidenceItem]:
        evidence: list[RelationshipEvidenceItem] = []
        for match in matches[:_MAX_EVIDENCE_ITEMS]:
            leader_activity_at = self._isoformat(match.leader_activity.activity_at)
            follower_activity_at = self._isoformat(match.follower_activity.activity_at)
            evidence.append(
                RelationshipEvidenceItem(
                    event_slug=match.event_slug,
                    condition_id=match.condition_id,
                    token_id=match.token_id,
                    side=match.side,
                    leader_activity_id=match.leader_activity.source_record_id,
                    follower_activity_id=match.follower_activity.source_record_id,
                    leader_activity_at=leader_activity_at,
                    follower_activity_at=follower_activity_at,
                    lag_seconds=match.lag_seconds,
                    leader_source_reference=match.leader_activity.source_reference,
                    follower_source_reference=match.follower_activity.source_reference,
                )
            )
        return evidence

    def _isoformat(self, value: datetime | None) -> str:
        assert value is not None
        return value.isoformat().replace("+00:00", "Z")

    def _activity_sort_key(
        self,
        activity: NormalizedWalletActivity,
    ) -> tuple[object, ...]:
        return (
            activity.wallet_address,
            activity.activity_at,
            activity.condition_id or "",
            activity.token_id or "",
            activity.side or "",
            activity.source_record_id,
        )

    def _report_sort_key(self, report: RelationshipReport) -> tuple[object, ...]:
        confidence = (
            report.confidence_score if report.confidence_score is not None else Decimal("-1")
        )
        return (
            0 if report.status == "accepted" else 1,
            -confidence,
            -report.matched_events_count,
            -report.matched_legs_count,
            report.leader_wallet,
            report.follower_wallet,
        )
