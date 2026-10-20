from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


def severity_for_score(score):
    """Standard 5x5 risk matrix banding (likelihood x impact)."""

    if score >= 15:
        return "extreme"
    if score >= 10:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


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

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("extreme", "Extreme"),
    ]

    LIKELIHOOD_CHOICES = [
        (1, "1 – Rare"),
        (2, "2 – Unlikely"),
        (3, "3 – Possible"),
        (4, "4 – Likely"),
        (5, "5 – Almost certain"),
    ]

    IMPACT_CHOICES = [
        (1, "1 – Negligible"),
        (2, "2 – Minor"),
        (3, "3 – Moderate"),
        (4, "4 – Major"),
        (5, "5 – Catastrophic"),
    ]

    description = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    likelihood = models.PositiveIntegerField(
        default=1,
        choices=LIKELIHOOD_CHOICES,
        validators=RATING_VALIDATORS,
    )
    impact = models.PositiveIntegerField(
        default=1,
        choices=IMPACT_CHOICES,
        validators=RATING_VALIDATORS,
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        editable=False,
        default="low",
    )

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

    class Meta:
        ordering = ["-likelihood", "-impact"]

    def __str__(self):
        return self.description

    @property
    def risk_score(self):
        return self.likelihood * self.impact

    def save(self, *args, **kwargs):
        self.severity = severity_for_score(self.risk_score)
        super().save(*args, **kwargs)
    
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

    @property
    def compliance_score(self):
        """Percentage of assessed controls met (partial counts as half)."""

        results = [
            control.result
            for control in self.controls.all()
            if control.result != "pending"
        ]

        if not results:
            return None

        points = sum(
            1 if result == "passed" else 0.5 if result == "partial" else 0
            for result in results
        )

        return round(points / len(results) * 100)

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

    source_incident = models.ForeignKey(
        "incidents.Incident",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
    )

    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_date"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return (
            self.status in ("open", "in_progress")
            and self.due_date < timezone.localdate()
        )

    def save(self, *args, **kwargs):

        now = timezone.now()

        if self.status in ("completed", "verified") and not self.completed_at:
            self.completed_at = now

        if self.status == "verified" and not self.verified_at:
            self.verified_at = now

        if self.status in ("open", "in_progress"):
            self.completed_at = None
            self.verified_at = None

        super().save(*args, **kwargs)