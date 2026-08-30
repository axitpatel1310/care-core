from django.db import models


class StaffMember(models.Model):
    EMPLOYMENT_STATUS = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("leave", "On Leave"),
    ]

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )

    employee_id = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=30, blank=True)

    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.CASCADE,
        related_name="staff",
    )

    ward = models.ForeignKey(
        "facility.Ward",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff",
    )

    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default="active",
    )

    qualifications = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
class ResidentStaffAssignment(models.Model):

    ROLE_CHOICES = [
        ("primary", "Primary Carer"),
        ("secondary", "Secondary Carer"),
        ("nurse", "Nurse"),
        ("manager", "Care Manager"),
        ("support", "Support Worker"),
    ]

    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name="resident_assignments",
    )

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="staff_assignments",
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="primary",
    )

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.staff} → {self.resident}"