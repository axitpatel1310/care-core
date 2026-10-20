from django.db import models


class Incident(models.Model):
    CATEGORY_CHOICES = [
        ("fall", "Fall"),
        ("medication_error", "Medication Error"),
        ("injury", "Injury"),
        ("missing_resident", "Missing Resident"),
        ("behavioural", "Behavioural Incident"),
        ("environmental", "Environmental Hazard"),
        ("other", "Other"),
    ]

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Investigating"),
        ("resolved", "Resolved"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
    )

    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="incidents",
        help_text="Set automatically from the resident; required for incidents not involving a resident.",
    )

    reported_by = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_incidents",
    )

    incident_date = models.DateTimeField()
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
    )

    description = models.TextField()
    immediate_action = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    investigation_notes = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)

    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Incident #{self.id} - {self.get_category_display()}"

    def save(self, *args, **kwargs):

        if self.resident_id and self.resident.facility_id:
            self.facility_id = self.resident.facility_id

        super().save(*args, **kwargs)