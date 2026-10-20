"""
Composite resident risk score.

Combines recent clinical signals into a 0–100 score with an explanation of
every contributing factor, so staff can see *why* a resident is flagged
rather than trusting an opaque number.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from care.models import Assessment, CarePlan, CareTask
from incidents.models import Incident
from medications.models import MedicationAdministration
from observations.models import Observation
from observations.news2 import (
    RISK_HIGH,
    RISK_LOW_MEDIUM,
    RISK_MEDIUM,
)


BAND_HIGH = "high"
BAND_MODERATE = "moderate"
BAND_LOW = "low"

BAND_THRESHOLDS = (
    (60, BAND_HIGH),
    (30, BAND_MODERATE),
    (0, BAND_LOW),
)

NEWS2_LOOKBACK_HOURS = 72
FALLS_LOOKBACK_DAYS = 90
INCIDENT_LOOKBACK_DAYS = 30
MEDICATION_LOOKBACK_DAYS = 14

NEWS2_POINTS = {
    RISK_HIGH: 30,
    RISK_MEDIUM: 20,
    RISK_LOW_MEDIUM: 12,
}

CARE_LEVEL_POINTS = {
    "complex": 10,
    "high": 5,
}


@dataclass
class RiskFactor:
    label: str
    points: int
    detail: str


@dataclass
class ResidentRisk:
    resident: object
    factors: list = field(default_factory=list)

    @property
    def score(self):
        return min(sum(factor.points for factor in self.factors), 100)

    @property
    def band(self):
        return band_for_score(self.score)

    def get_band_display(self):
        return self.band.capitalize()

    def add(self, label, points, detail):
        if points > 0:
            self.factors.append(RiskFactor(label, points, detail))


def band_for_score(score):
    for threshold, band in BAND_THRESHOLDS:
        if score >= threshold:
            return band
    return BAND_LOW


class _Signals:
    """
    All the data the score needs for a set of residents, fetched with a
    fixed number of grouped queries rather than several queries per resident.
    """

    def __init__(self, resident_ids, now):

        today = timezone.localdate(now)

        self.latest_obs = {}

        for observation in (
            Observation.objects
            .filter(
                resident_id__in=resident_ids,
                recorded_at__gte=now - timedelta(hours=NEWS2_LOOKBACK_HOURS),
            )
            .order_by("resident_id", "-recorded_at")
        ):
            self.latest_obs.setdefault(observation.resident_id, observation)

        incidents = Incident.objects.filter(resident_id__in=resident_ids)

        self.falls = self._count(
            incidents.filter(
                category="fall",
                incident_date__gte=now - timedelta(days=FALLS_LOOKBACK_DAYS),
            ),
            "resident_id",
        )

        self.serious = self._count(
            incidents.filter(
                severity__in=["high", "critical"],
                incident_date__gte=now - timedelta(days=INCIDENT_LOOKBACK_DAYS),
            ).exclude(category="fall"),
            "resident_id",
        )

        self.doses = defaultdict(Counter)

        for row in (
            MedicationAdministration.objects
            .filter(
                medication__resident_id__in=resident_ids,
                administered_at__gte=now - timedelta(days=MEDICATION_LOOKBACK_DAYS),
            )
            .values("medication__resident_id", "status")
            .annotate(total=Count("id"))
        ):
            self.doses[row["medication__resident_id"]][row["status"]] += row["total"]

        self.overdue_tasks = self._count(
            CareTask.objects.filter(
                resident_id__in=resident_ids,
                status__in=["pending", "in_progress"],
                due_date__lt=today,
            ),
            "resident_id",
        )

        self.active_plan = {}

        for plan in (
            CarePlan.objects
            .filter(resident_id__in=resident_ids, status="active")
            .order_by("resident_id", "-created_at")
            .only("resident_id", "next_review", "created_at")
        ):
            self.active_plan.setdefault(plan.resident_id, plan)

        self.overdue_assessments = self._count(
            Assessment.objects.filter(
                resident_id__in=resident_ids,
                next_review__lt=today,
            ),
            "resident_id",
        )

    @staticmethod
    def _count(queryset, key):
        return dict(
            queryset.values(key).annotate(total=Count("id")).values_list(key, "total")
        )


def _score(resident, signals, today):

    risk = ResidentRisk(resident=resident)

    # 1. Latest NEWS2 within the lookback window.
    latest_obs = signals.latest_obs.get(resident.pk)

    if latest_obs:
        points = NEWS2_POINTS.get(latest_obs.risk_level)

        if points is None and latest_obs.news2_score > 0:
            points = 4

        risk.add(
            "Early warning score",
            points or 0,
            f"Latest NEWS2 {latest_obs.news2_score} "
            f"({latest_obs.get_risk_level_display()} risk)",
        )

    # 2. Falls history.
    falls = signals.falls.get(resident.pk, 0)

    risk.add(
        "Falls history",
        min(falls * 10, 25),
        f"{falls} fall{'s' if falls != 1 else ''} in the last {FALLS_LOOKBACK_DAYS} days",
    )

    # 3. Recent serious incidents (excluding falls, already counted).
    serious = signals.serious.get(resident.pk, 0)

    risk.add(
        "Serious incidents",
        min(serious * 10, 15),
        f"{serious} high/critical incident{'s' if serious != 1 else ''} "
        f"in the last {INCIDENT_LOOKBACK_DAYS} days",
    )

    # 4. Medication non-adherence.
    doses = signals.doses.get(resident.pk)

    if doses:
        total = sum(doses.values())
        not_given = sum(doses[status] for status in ("missed", "refused", "withheld"))
        ratio = not_given / total

        risk.add(
            "Medication adherence",
            round(ratio * 20),
            f"{not_given} of {total} doses not given "
            f"({round((1 - ratio) * 100)}% adherence)",
        )

    # 5. Overdue care tasks.
    overdue_tasks = signals.overdue_tasks.get(resident.pk, 0)

    risk.add(
        "Overdue care tasks",
        min(overdue_tasks * 3, 10),
        f"{overdue_tasks} overdue task{'s' if overdue_tasks != 1 else ''}",
    )

    # 6. Care complexity.
    risk.add(
        "Care complexity",
        CARE_LEVEL_POINTS.get(resident.care_level, 0),
        f"{resident.get_care_level_display()} care level",
    )

    # 7. Governance gaps: overdue reviews.
    active_plan = signals.active_plan.get(resident.pk)

    if active_plan is None:
        risk.add("Care plan", 5, "No active care plan")
    elif active_plan.next_review and active_plan.next_review < today:
        risk.add(
            "Care plan",
            5,
            f"Review overdue since {active_plan.next_review:%d %b %Y}",
        )

    overdue_assessments = signals.overdue_assessments.get(resident.pk, 0)

    risk.add(
        "Assessments",
        min(overdue_assessments * 5, 10),
        f"{overdue_assessments} assessment review{'s' if overdue_assessments != 1 else ''} overdue",
    )

    risk.factors.sort(key=lambda factor: factor.points, reverse=True)

    return risk


def assess_residents(residents, now=None):
    """Score many residents with a constant number of queries, highest risk first."""

    now = now or timezone.now()
    residents = list(residents)

    signals = _Signals([resident.pk for resident in residents], now)
    today = timezone.localdate(now)

    assessments = [_score(resident, signals, today) for resident in residents]
    assessments.sort(key=lambda item: item.score, reverse=True)

    return assessments


def assess_resident(resident, now=None):
    return assess_residents([resident], now=now)[0]
