"""
Scheduled-dose logic for the Medication Administration Record (MAR).

A scheduled dose is (medication, day, dose time). Its state is worked out
from the administration recorded against it, or, when nothing has been
recorded, from how far the scheduled time is from now.
"""

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Medication, MedicationAdministration


# How long before / after the scheduled time a dose counts as "due now".
DUE_WINDOW = timedelta(minutes=60)

STATE_LABELS = {
    "administered": "Given",
    "refused": "Refused",
    "missed": "Missed",
    "withheld": "Withheld",
    "overdue": "Overdue",
    "due": "Due now",
    "upcoming": "Upcoming",
}


FREQUENCY_PATTERNS = [
    (r"\b(prn|as required|as needed|when required)\b", None),
    (r"\b(four times|qds|qid|4 ?x)\b", ["08:00", "12:00", "16:00", "20:00"]),
    (r"\b(three times|tds|tid|3 ?x)\b", ["08:00", "14:00", "20:00"]),
    (r"\b(twice|bd|bid|2 ?x)\b", ["08:00", "20:00"]),
    (r"\b(night|nocte|bedtime)\b", ["21:00"]),
    (r"\b(once|daily|od|mane|morning)\b", ["08:00"]),
]


def default_times_for_frequency(frequency):
    """
    Suggest dose times from a free-text frequency such as "Twice daily".
    Returns None for PRN medicines and [] when nothing matches.
    """

    text = (frequency or "").lower()

    for pattern, times in FREQUENCY_PATTERNS:
        if re.search(pattern, text):
            return times

    return []


def parse_dose_times(value):
    """Parse "08:00, 20:00" into sorted, de-duplicated time objects."""

    times = set()

    for part in re.split(r"[,;\s]+", value or ""):
        if not part:
            continue

        match = re.fullmatch(r"([01]?\d|2[0-3])[:.]?([0-5]\d)", part)

        if not match:
            raise ValueError(f"'{part}' is not a valid 24-hour time (use HH:MM).")

        times.add(time(int(match.group(1)), int(match.group(2))))

    return sorted(times)


@dataclass
class ScheduledDose:
    medication: Medication
    scheduled_for: datetime
    administration: MedicationAdministration = None
    state: str = "upcoming"

    @property
    def state_label(self):
        return STATE_LABELS[self.state]

    @property
    def is_outstanding(self):
        return self.state in ("due", "overdue")


def dose_state(scheduled_for, administration, now):

    if administration is not None:
        return administration.status

    if now > scheduled_for + DUE_WINDOW:
        return "overdue"

    if now >= scheduled_for - DUE_WINDOW:
        return "due"

    return "upcoming"


def scheduled_datetime(day, dose_time):
    return timezone.make_aware(
        datetime.combine(day, dose_time),
        timezone.get_current_timezone(),
    )


def scheduled_doses(medications, start_day, end_day, now=None):
    """
    Every scheduled dose for the given medications between start_day and
    end_day inclusive, each matched to its recorded administration.
    """

    now = now or timezone.now()

    medications = [
        medication for medication in medications
        if not medication.as_required
    ]

    if not medications:
        return []

    recorded = {
        (administration.medication_id, administration.scheduled_for): administration
        for administration in MedicationAdministration.objects.filter(
            medication__in=medications,
            scheduled_for__date__gte=start_day - timedelta(days=1),
            scheduled_for__date__lte=end_day + timedelta(days=1),
        ).select_related("administered_by__user")
    }

    doses = []
    day = start_day

    while day <= end_day:

        for medication in medications:

            if not medication.is_active_on(day):
                continue

            for dose_time in medication.dose_times.all():

                when = scheduled_datetime(day, dose_time.time)
                administration = recorded.get((medication.pk, when))

                doses.append(ScheduledDose(
                    medication=medication,
                    scheduled_for=when,
                    administration=administration,
                    state=dose_state(when, administration, now),
                ))

        day += timedelta(days=1)

    doses.sort(key=lambda dose: (dose.scheduled_for, str(dose.medication.resident)))

    return doses


def active_medications(queryset=None):

    queryset = queryset if queryset is not None else Medication.objects.all()

    return (
        queryset
        .filter(status="active", as_required=False)
        .select_related("resident")
        .prefetch_related("dose_times")
    )


def doses_for_day(day, queryset=None, now=None):
    return scheduled_doses(active_medications(queryset), day, day, now=now)


def overdue_doses(now=None, queryset=None):
    """Today's scheduled doses with nothing recorded, past their due window."""

    now = now or timezone.now()
    today = timezone.localdate(now)

    return [
        dose for dose in doses_for_day(today, queryset, now=now)
        if dose.state == "overdue"
    ]
