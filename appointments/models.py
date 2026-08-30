from django.db import models


class Appointment(models.Model):

    TYPE_CHOICES = [
        ("medical", "Medical"),
        ("dental", "Dental"),
        ("therapy", "Therapy"),
        ("hospital", "Hospital"),
        ("specialist", "Specialist"),
        ("family", "Family Visit"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("missed", "Missed"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="appointments",
    )

    assigned_staff = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )

    title = models.CharField(
        max_length=200,
    )

    appointment_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default="other",
    )

    appointment_date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField(
        null=True,
        blank=True,
    )

    location = models.CharField(
        max_length=255,
        blank=True,
    )

    provider = models.CharField(
        max_length=200,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
    )

    notes = models.TextField(
        blank=True,
    )

    outcome = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.title} - {self.resident}"

    class Meta:
        ordering = [
            "appointment_date",
            "start_time",
        ]