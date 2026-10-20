from django.db import models


class Resident(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("hospital", "Hospital"),
        ("leave", "On Leave"),
        ("discharged", "Discharged"),
        ("deceased", "Deceased"),
    ]

    CARE_LEVEL_CHOICES = [
        ("standard", "Standard"),
        ("high", "High"),
        ("complex", "Complex"),
    ]

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("unknown", "Prefer not to say"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
    )

    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="residents",
        help_text="Set automatically from the room; choose it directly for residents without a room yet.",
    )

    room = models.ForeignKey(
        "facility.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="residents",
    )

    admission_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    care_level = models.CharField(
        max_length=20,
        choices=CARE_LEVEL_CHOICES,
        default="standard",
    )

    mobility_needs = models.TextField(blank=True)
    nutrition_needs = models.TextField(blank=True)
    communication_needs = models.TextField(blank=True)
    cognitive_support_needs = models.TextField(blank=True)
    behavioural_support_needs = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):

        # The room's facility always wins, so the two can never disagree.
        if self.room_id:
            self.facility_id = (
                type(self.room).objects
                .filter(pk=self.room_id)
                .values_list("ward__facility_id", flat=True)
                .first()
            )

        super().save(*args, **kwargs)
    
class ResidentContact(models.Model):

    CONTACT_TYPES = [
        ("emergency", "Emergency Contact"),
        ("family", "Family / Representative"),
    ]

    resident = models.ForeignKey(
        Resident,
        on_delete=models.CASCADE,
        related_name="contacts",
    )

    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPES,
    )

    name = models.CharField(max_length=200)

    relationship = models.CharField(max_length=100)

    phone = models.CharField(max_length=30)

    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.resident}"