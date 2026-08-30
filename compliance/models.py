from django.db import models


class ComplianceDocument(models.Model):
    DOCUMENT_TYPES = [
        ("policy", "Policy"),
        ("procedure", "Procedure"),
        ("guideline", "Guideline"),
        ("standard", "Standard"),
        ("audit", "Audit Document"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("draft", "Draft"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES,
    )
    version = models.CharField(max_length=50)

    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="compliance_documents",
    )

    created_at = models.DateField(auto_now_add=True)
    last_reviewed = models.DateField(null=True, blank=True)
    next_review = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )

    file = models.FileField(
        upload_to="compliance_documents/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.title
    
class Risk(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("monitoring", "Monitoring"),
        ("resolved", "Resolved"),
    ]

    CATEGORY_CHOICES = [
        ("clinical", "Clinical"),
        ("staff", "Staff"),
        ("medication", "Medication"),
        ("environment", "Environment"),
        ("compliance", "Compliance"),
        ("other", "Other"),
    ]

    description = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    likelihood = models.PositiveIntegerField(default=1)
    impact = models.PositiveIntegerField(default=1)

    severity = models.CharField(max_length=20)

    owner = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_risks",
    )

    mitigation = models.TextField(blank=True)
    review_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
    
class Audit(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_audits",
    )

    start_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
    )

    def __str__(self):
        return self.title
    
class AuditControl(models.Model):
    RESULT_CHOICES = [
        ("pending", "Pending"),
        ("passed", "Passed"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ]

    audit = models.ForeignKey(
        Audit,
        on_delete=models.CASCADE,
        related_name="controls",
    )

    requirement = models.TextField()
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default="pending",
    )

    evidence = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    finding = models.TextField(blank=True)

    def __str__(self):
        return f"{self.audit.title} - {self.requirement[:40]}"
    
class CorrectiveAction(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("verified", "Verified"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        "staff.StaffMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="medium",
    )

    due_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    source_finding = models.ForeignKey(
        AuditControl,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
    )

    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title