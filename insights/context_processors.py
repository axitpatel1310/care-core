from django.core.cache import cache
from django.utils import timezone

from .alerts import CRITICAL, alerts_for


ALERT_CACHE_SECONDS = 60


def alert_cache_key(user):
    return f"carecore:alert-summary:{user.pk}"


def alerts(request):
    """Expose a cached alert summary for the notification bell on every page."""

    user = getattr(request, "user", None)

    if user is None or not user.is_authenticated:
        return {}

    key = alert_cache_key(user)
    summary = cache.get(key)

    if summary is None:

        user_alerts = alerts_for(user)

        summary = {
            "total": len(user_alerts),
            "critical": sum(1 for alert in user_alerts if alert.severity == CRITICAL),
        }

        cache.set(key, summary, ALERT_CACHE_SECONDS)

    return {
        "alert_summary": summary,
        "today": timezone.localdate(),
    }
