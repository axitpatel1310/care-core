from django.db import models


class Medication(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("stopped", "Stopped"),
        ("completed", "Completed"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="medications",
    )

    name = models.CharField(max_length=200)
    dose = models.CharField(max_length=100)
    route = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    prescriber = models.CharField(max_length=200, blank=True)

    as_required = models.BooleanField(
        "PRN (as required)",
        default=False,
        help_text="PRN medicines have no scheduled dose times.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    def __str__(self):
        return f"{self.name} - {self.resident}"

    def is_active_on(self, day):
        return (
            self.status == "active"
            and self.start_date <= day
            and (self.end_date is None or self.end_date >= day)
        )

    @property
    def schedule_display(self):
        if self.as_required:
            return "As required (PRN)"
        times = [dose.time.strftime("%H:%M") for dose in self.dose_times.all()]
        return ", ".join(times) or "No dose times set"


class MedicationDoseTime(models.Model):
    """A time of day at which a scheduled dose of a medication is due."""

    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name="dose_times",
    )

    time = models.TimeField()

    class Meta:
        ordering = ["time"]
        constraints = [
            models.UniqueConstraint(
                fields=["medication", "time"],
                name="unique_medication_dose_time",
            ),
        ]

    def __str__(self):
        return f"{self.medication.name} at {self.time:%H:%M}"
    
class MedicationAdministration(models.Model):
    STATUS_CHOICES = [
        ("administered", "Administered"),
        ("missed", "Missed"),
        ("refused", "Refused"),
        ("withheld", "Withheld"),
    ]

    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name="administrations",
    )

    administered_by = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        related_name="medication_administrations",
    )

    administered_at = models.DateTimeField()

    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The scheduled dose this record answers; empty for PRN or unscheduled doses.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
    )

    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["medication", "scheduled_for"]),
        ]

    def __str__(self):
        return f"{self.medication} - {self.status}"