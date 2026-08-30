from django.db import models


class CarePlan(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("draft", "Draft"),
        ("archived", "Archived"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="care_plans",
    )

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_care_plans",
    )

    responsible_staff = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsible_care_plans",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed = models.DateField(null=True, blank=True)
    next_review = models.DateField(null=True, blank=True)

    mobility = models.TextField(blank=True)
    nutrition = models.TextField(blank=True)
    personal_care = models.TextField(blank=True)
    communication = models.TextField(blank=True)
    cognitive_support = models.TextField(blank=True)
    behavioural_support = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Care Plan - {self.resident}"
    
class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ("mobility", "Mobility"),
        ("falls", "Falls Risk"),
        ("nutrition", "Nutrition"),
        ("pain", "Pain"),
        ("skin", "Skin"),
        ("cognitive", "Cognitive"),
        ("behavioural", "Behavioural"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="assessments",
    )

    assessment_type = models.CharField(
        max_length=30,
        choices=ASSESSMENT_TYPES,
    )

    assessment_date = models.DateField()
    performed_by = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        related_name="assessments",
    )

    result = models.TextField()
    notes = models.TextField(blank=True)
    next_review = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_assessment_type_display()} - {self.resident}"
    
    
class CognitiveBehaviouralSupport(models.Model):
    resident = models.OneToOneField(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="cognitive_support",
    )

    support_requirements = models.TextField(blank=True)
    known_triggers = models.TextField(blank=True)
    communication_preferences = models.TextField(blank=True)
    behaviour_observations = models.TextField(blank=True)
    de_escalation_strategies = models.TextField(blank=True)
    care_instructions = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Support - {self.resident}"
    
class CareTask(models.Model):

    TASK_TYPE_CHOICES = [
        ("personal_care", "Personal Care"),
        ("medication", "Medication"),
        ("meal", "Meal / Nutrition"),
        ("mobility", "Mobility"),
        ("health_check", "Health Check"),
        ("appointment", "Appointment"),
        ("documentation", "Documentation"),
        ("other", "Other"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    resident = models.ForeignKey(
        "residents.Resident",
        on_delete=models.CASCADE,
        related_name="care_tasks",
    )

    assigned_to = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="care_tasks",
    )

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField(
        blank=True,
    )

    task_type = models.CharField(
        max_length=30,
        choices=TASK_TYPE_CHOICES,
        default="other",
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
    )

    due_date = models.DateField()

    due_time = models.TimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_by = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_care_tasks",
    )

    notes = models.TextField(
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
        ordering = ["due_date", "due_time"]