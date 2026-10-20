"""
Sign-in throttling.

Attempts are stored in the LoginAttempt table, so every server process
(e.g. several gunicorn workers) sees the same counts. An email is locked
after too many failures since its last successful sign-in within the
window; an IP address is locked after too many failures of any account.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import LoginAttempt


WINDOW_SECONDS = getattr(settings, "LOGIN_THROTTLE_WINDOW", 15 * 60)
MAX_FAILURES_PER_EMAIL = getattr(settings, "LOGIN_THROTTLE_EMAIL_LIMIT", 5)
MAX_FAILURES_PER_IP = getattr(settings, "LOGIN_THROTTLE_IP_LIMIT", 20)

# Attempts older than this are deleted as new ones are recorded.
RETENTION = timedelta(days=30)


def _normalise(email):
    return (email or "").strip().lower()


def _window_start():
    return timezone.now() - timedelta(seconds=WINDOW_SECONDS)


def failures_for_email(email):

    email = _normalise(email)
    attempts = LoginAttempt.objects.filter(email=email, created_at__gte=_window_start())

    last_success = attempts.filter(successful=True).order_by("-created_at").first()

    failures = attempts.filter(successful=False)

    if last_success:
        failures = failures.filter(created_at__gt=last_success.created_at)

    return failures.count()


def failures_for_ip(ip):

    if not ip:
        return 0

    return LoginAttempt.objects.filter(
        ip_address=ip,
        successful=False,
        created_at__gte=_window_start(),
    ).count()


def is_locked(email, ip):
    return (
        failures_for_email(email) >= MAX_FAILURES_PER_EMAIL
        or failures_for_ip(ip) >= MAX_FAILURES_PER_IP
    )


def record(email, ip, successful):

    LoginAttempt.objects.filter(created_at__lt=timezone.now() - RETENTION).delete()

    LoginAttempt.objects.create(
        email=_normalise(email)[:254],
        ip_address=ip or None,
        successful=successful,
    )


def register_failure(email, ip):
    record(email, ip, successful=False)


def register_success(email, ip):
    record(email, ip, successful=True)


def lockout_minutes():
    return WINDOW_SECONDS // 60
