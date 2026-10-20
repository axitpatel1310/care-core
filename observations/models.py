from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .news2 import RISK_CHOICES, calculate_news2


class Observation(models.Model):

    CONSCIOUSNESS_CHOICES = [
        ("A", "Alert"),
        ("C", "New confusion"),
        ("V", "Responds to voice"),
        ("P", "Responds to pain"),
        ("U", "Unresponsive"),
    ]

    SPO2_SCALE_CHOICES = [
        (1, "Scale 1 (standard)"),
        (2, "Scale 2 (target 88–92%, e.g. hypercapnic COPD)"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="observations",
    )

    recorded_by = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )

    recorded_at = models.DateTimeField(
        default=timezone.now,
    )

    respiratory_rate = models.PositiveSmallIntegerField(
        help_text="Breaths per minute",
        validators=[MinValueValidator(1), MaxValueValidator(80)],
    )

    spo2 = models.PositiveSmallIntegerField(
        "SpO₂ (%)",
        validators=[MinValueValidator(50), MaxValueValidator(100)],
    )

    spo2_scale = models.PositiveSmallIntegerField(
        "SpO₂ scale",
        choices=SPO2_SCALE_CHOICES,
        default=1,
    )

    on_oxygen = models.BooleanField(
        "On supplemental oxygen",
        default=False,
    )

    systolic_bp = models.PositiveSmallIntegerField(
        "Systolic BP (mmHg)",
        validators=[MinValueValidator(40), MaxValueValidator(300)],
    )

    diastolic_bp = models.PositiveSmallIntegerField(
        "Diastolic BP (mmHg)",
        null=True,
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(200)],
    )

    pulse = models.PositiveSmallIntegerField(
        "Pulse (bpm)",
        validators=[MinValueValidator(20), MaxValueValidator(250)],
    )

    consciousness = models.CharField(
        max_length=1,
        choices=CONSCIOUSNESS_CHOICES,
        default="A",
    )

    temperature = models.DecimalField(
        "Temperature (°C)",
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(25), MaxValueValidator(45)],
    )

    blood_glucose = models.DecimalField(
        "Blood glucose (mmol/L)",
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    pain_score = models.PositiveSmallIntegerField(
        "Pain score (0–10)",
        null=True,
        blank=True,
        validators=[MaxValueValidator(10)],
    )

    notes = models.TextField(
        blank=True,
    )

    news2_score = models.PositiveSmallIntegerField(
        "NEWS2 score",
        editable=False,
        default=0,
    )

    risk_level = models.CharField(
        max_length=20,
        choices=RISK_CHOICES,
        editable=False,
        default="low",
    )

    has_red_score = models.BooleanField(
        editable=False,
        default=False,
    )

    escalation_task = models.ForeignKey(
        "care.CareTask",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="source_observations",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["resident", "-recorded_at"]),
        ]

    def __str__(self):
        return f"NEWS2 {self.news2_score} - {self.resident} ({self.recorded_at:%d %b %Y %H:%M})"

    def calculate(self):

        return calculate_news2(
            respiratory_rate=self.respiratory_rate,
            spo2=self.spo2,
            on_oxygen=self.on_oxygen,
            systolic_bp=self.systolic_bp,
            pulse=self.pulse,
            consciousness=self.consciousness,
            temperature=self.temperature,
            spo2_scale=self.spo2_scale,
        )

    def save(self, *args, **kwargs):

        result = self.calculate()

        self.news2_score = result.total
        self.risk_level = result.risk_level
        self.has_red_score = result.has_red_score

        super().save(*args, **kwargs)

    @property
    def result(self):
        return self.calculate()
