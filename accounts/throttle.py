"""
Sign-in throttling.

Failed attempts are counted per email address and per client IP in the
cache. Once a limit is reached further attempts are refused until the
window expires, which blocks online password guessing without locking
the account in the database.
"""

from django.conf import settings
from django.core.cache import cache


WINDOW_SECONDS = getattr(settings, "LOGIN_THROTTLE_WINDOW", 15 * 60)
MAX_FAILURES_PER_EMAIL = getattr(settings, "LOGIN_THROTTLE_EMAIL_LIMIT", 5)
MAX_FAILURES_PER_IP = getattr(settings, "LOGIN_THROTTLE_IP_LIMIT", 20)


def _keys(email, ip):
    return (
        f"carecore:login-fail:email:{email.strip().lower()}",
        f"carecore:login-fail:ip:{ip or 'unknown'}",
    )


def is_locked(email, ip):

    email_key, ip_key = _keys(email, ip)

    return (
        cache.get(email_key, 0) >= MAX_FAILURES_PER_EMAIL
        or cache.get(ip_key, 0) >= MAX_FAILURES_PER_IP
    )


def register_failure(email, ip):

    for key in _keys(email, ip):
        # add() starts the window on the first failure; incr() keeps its expiry.
        if not cache.add(key, 1, WINDOW_SECONDS):
            try:
                cache.incr(key)
            except ValueError:
                cache.set(key, 1, WINDOW_SECONDS)


def reset(email):
    cache.delete(_keys(email, None)[0])


def lockout_minutes():
    return WINDOW_SECONDS // 60
