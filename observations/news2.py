"""
NEWS2 (National Early Warning Score 2) calculation.

Implements the scoring chart and clinical response thresholds published by
the Royal College of Physicians (2017). Every function here is pure so the
scoring rules can be unit tested in isolation from the database.
"""

from dataclasses import dataclass, field
from decimal import Decimal


RISK_LOW = "low"
RISK_LOW_MEDIUM = "low_medium"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

RISK_CHOICES = [
    (RISK_LOW, "Low"),
    (RISK_LOW_MEDIUM, "Low–Medium"),
    (RISK_MEDIUM, "Medium"),
    (RISK_HIGH, "High"),
]

CONSCIOUSNESS_ALERT = "A"

# Minimum monitoring frequency (hours) and clinical response for each risk band.
CLINICAL_RESPONSE = {
    RISK_LOW: {
        "monitoring_hours": 12,
        "response": "Continue routine monitoring (minimum every 12 hours).",
    },
    RISK_LOW_MEDIUM: {
        "monitoring_hours": 1,
        "response": (
            "Single parameter scored 3: increase monitoring to at least hourly "
            "and the registered nurse must inform the medical team."
        ),
    },
    RISK_MEDIUM: {
        "monitoring_hours": 1,
        "response": (
            "Urgent response: monitor at least hourly and request an urgent "
            "review by a clinician with competence in acute illness."
        ),
    },
    RISK_HIGH: {
        "monitoring_hours": 0,
        "response": (
            "Emergency response: continuous monitoring and immediate "
            "emergency assessment (consider transfer / call emergency services)."
        ),
    },
}


@dataclass
class News2Result:
    total: int
    risk_level: str
    has_red_score: bool
    breakdown: dict = field(default_factory=dict)

    @property
    def monitoring_hours(self):
        return CLINICAL_RESPONSE[self.risk_level]["monitoring_hours"]

    @property
    def response(self):
        return CLINICAL_RESPONSE[self.risk_level]["response"]

    @property
    def requires_escalation(self):
        return self.risk_level != RISK_LOW


def score_respiratory_rate(rate):
    if rate <= 8:
        return 3
    if rate <= 11:
        return 1
    if rate <= 20:
        return 0
    if rate <= 24:
        return 2
    return 3


def score_spo2_scale_1(spo2):
    if spo2 <= 91:
        return 3
    if spo2 <= 93:
        return 2
    if spo2 <= 95:
        return 1
    return 0


def score_spo2_scale_2(spo2, on_oxygen):
    """Scale 2 is for residents with a prescribed 88–92% target (e.g. hypercapnic COPD)."""

    if spo2 <= 83:
        return 3
    if spo2 <= 85:
        return 2
    if spo2 <= 87:
        return 1
    if spo2 <= 92 or not on_oxygen:
        return 0
    if spo2 <= 94:
        return 1
    if spo2 <= 96:
        return 2
    return 3


def score_air_or_oxygen(on_oxygen):
    return 2 if on_oxygen else 0


def score_systolic_bp(systolic):
    if systolic <= 90:
        return 3
    if systolic <= 100:
        return 2
    if systolic <= 110:
        return 1
    if systolic <= 219:
        return 0
    return 3


def score_pulse(pulse):
    if pulse <= 40:
        return 3
    if pulse <= 50:
        return 1
    if pulse <= 90:
        return 0
    if pulse <= 110:
        return 1
    if pulse <= 130:
        return 2
    return 3


def score_consciousness(level):
    return 0 if level == CONSCIOUSNESS_ALERT else 3


def score_temperature(temperature):
    temperature = Decimal(str(temperature))

    if temperature <= Decimal("35.0"):
        return 3
    if temperature <= Decimal("36.0"):
        return 1
    if temperature <= Decimal("38.0"):
        return 0
    if temperature <= Decimal("39.0"):
        return 1
    return 2


def risk_level_for(total, has_red_score):
    if total >= 7:
        return RISK_HIGH
    if total >= 5:
        return RISK_MEDIUM
    if has_red_score:
        return RISK_LOW_MEDIUM
    return RISK_LOW


def calculate_news2(
    respiratory_rate,
    spo2,
    on_oxygen,
    systolic_bp,
    pulse,
    consciousness,
    temperature,
    spo2_scale=1,
):

    if spo2_scale == 2:
        spo2_score = score_spo2_scale_2(spo2, on_oxygen)
    else:
        spo2_score = score_spo2_scale_1(spo2)

    breakdown = {
        "respiratory_rate": score_respiratory_rate(respiratory_rate),
        "spo2": spo2_score,
        "air_or_oxygen": score_air_or_oxygen(on_oxygen),
        "systolic_bp": score_systolic_bp(systolic_bp),
        "pulse": score_pulse(pulse),
        "consciousness": score_consciousness(consciousness),
        "temperature": score_temperature(temperature),
    }

    total = sum(breakdown.values())
    has_red_score = any(value == 3 for value in breakdown.values())

    return News2Result(
        total=total,
        risk_level=risk_level_for(total, has_red_score),
        has_red_score=has_red_score,
        breakdown=breakdown,
    )
