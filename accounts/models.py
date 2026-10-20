from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("rn", "Registered Nurse"),
        ("en", "Enrolled Nurse"),
        ("care_worker", "Personal Care Worker"),
        ("admin", "Administrator"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="care_worker",
    )

    def __str__(self):
        return self.get_full_name() or self.username
    
    
class AuditLog(models.Model):

    ACTION_CHOICES = [
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
        ("login", "Logged In"),
        ("logout", "Logged Out"),
        ("login_failed", "Failed Login"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
    )

    module = models.CharField(
        max_length=100,
    )

    object_type = models.CharField(
        max_length=100,
        blank=True,
    )

    object_id = models.CharField(
        max_length=100,
        blank=True,
    )

    description = models.TextField()

    changes = models.JSONField(
        default=dict,
        blank=True,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.module}"


class LoginAttempt(models.Model):
    """
    Sign-in attempts, stored in the database so the throttle is shared by
    every server process (an in-memory cache would count per process).
    """

    email = models.CharField(max_length=254, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    successful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        outcome = "success" if self.successful else "failure"
        return f"{self.email} {outcome} at {self.created_at:%Y-%m-%d %H:%M}"
