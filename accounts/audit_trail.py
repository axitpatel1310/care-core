"""
Automatic audit trail.

Every create, update and delete of a tracked model is written to AuditLog
with the acting user, client IP and a field-level diff for updates, so
the log does not depend on each view remembering to record its changes.
"""

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import post_delete, post_save, pre_save

from .middleware import get_current_request
from .models import AuditLog


TRACKED_MODELS = [
    "residents.Resident",
    "residents.ResidentContact",
    "staff.StaffMember",
    "staff.ResidentStaffAssignment",
    "care.CarePlan",
    "care.Assessment",
    "care.CognitiveBehaviouralSupport",
    "care.CareTask",
    "medications.Medication",
    "medications.MedicationAdministration",
    "incidents.Incident",
    "appointments.Appointment",
    "observations.Observation",
    "facility.Facility",
    "facility.Ward",
    "facility.Room",
    "compliance.ComplianceDocument",
    "compliance.Risk",
    "compliance.Audit",
    "compliance.AuditControl",
    "compliance.CorrectiveAction",
]

IGNORED_FIELDS = {"created_at", "updated_at"}


def client_ip(request):

    if request is None:
        return None

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def request_user(request):

    user = getattr(request, "user", None)

    if user is not None and user.is_authenticated:
        return user

    return None


def snapshot(instance):

    return {
        field.attname: field.value_from_object(instance)
        for field in instance._meta.concrete_fields
        if field.attname not in IGNORED_FIELDS
    }


def serialise(value):

    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    return str(value)


def write_log(action, instance, description, changes=None):

    request = get_current_request()

    AuditLog.objects.create(
        user=request_user(request),
        action=action,
        module=instance._meta.app_label,
        object_type=instance._meta.object_name,
        object_id=str(instance.pk or ""),
        description=description,
        changes=changes or {},
        ip_address=client_ip(request),
    )


def capture_previous_state(sender, instance, raw=False, **kwargs):

    if raw or not instance.pk:
        instance._audit_previous = None
        return

    previous = sender._default_manager.filter(pk=instance.pk).first()
    instance._audit_previous = snapshot(previous) if previous else None


def log_save(sender, instance, created, raw=False, **kwargs):

    if raw:
        return

    label = sender._meta.verbose_name

    if created:
        write_log("create", instance, f"Created {label}: {instance}")
        return

    previous = getattr(instance, "_audit_previous", None) or {}
    current = snapshot(instance)

    changes = {
        name: [serialise(previous.get(name)), serialise(value)]
        for name, value in current.items()
        if name in previous and previous.get(name) != value
    }

    if not changes:
        return

    fields = ", ".join(name.replace("_id", "").replace("_", " ") for name in changes)

    write_log("update", instance, f"Updated {label}: {instance} ({fields})", changes)


def log_delete(sender, instance, **kwargs):

    write_log("delete", instance, f"Deleted {sender._meta.verbose_name}: {instance}")


def log_login(sender, request, user, **kwargs):

    AuditLog.objects.create(
        user=user,
        action="login",
        module="accounts",
        object_type="User",
        object_id=str(user.pk),
        description=f"{user} signed in.",
        ip_address=client_ip(request),
    )


def log_logout(sender, request, user, **kwargs):

    if user is None:
        return

    AuditLog.objects.create(
        user=user,
        action="logout",
        module="accounts",
        object_type="User",
        object_id=str(user.pk),
        description=f"{user} signed out.",
        ip_address=client_ip(request),
    )


def log_login_failed(sender, credentials, request=None, **kwargs):

    AuditLog.objects.create(
        action="login_failed",
        module="accounts",
        description=f"Failed sign-in attempt for '{credentials.get('username', '')}'.",
        ip_address=client_ip(request),
    )


def connect(apps):

    for label in TRACKED_MODELS:

        model = apps.get_model(label)
        uid = f"audit-{label}"

        pre_save.connect(capture_previous_state, sender=model, dispatch_uid=f"{uid}-pre")
        post_save.connect(log_save, sender=model, dispatch_uid=f"{uid}-save")
        post_delete.connect(log_delete, sender=model, dispatch_uid=f"{uid}-delete")

    user_logged_in.connect(log_login, dispatch_uid="audit-login")
    user_logged_out.connect(log_logout, dispatch_uid="audit-logout")
    user_login_failed.connect(log_login_failed, dispatch_uid="audit-login-failed")
