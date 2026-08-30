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

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    def __str__(self):
        return f"{self.name} - {self.resident}"
    
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
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medication} - {self.status}"