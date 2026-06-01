from django.core.cache import cache
from django.utils import timezone
from core.interfaces.http.utils.ip import get_client_ip
from core.infrastructure.models import SuspiciousActivity, SuspiciousEvent


def _get_activity(request):
    ip = get_client_ip(request) or "0.0.0.0"
    user = getattr(request, "user", None)
    user = user if getattr(user, "is_authenticated", False) else None
    obj = SuspiciousActivity.objects.filter(ip=ip, user=user).first()
    if not obj:
        obj = SuspiciousActivity.objects.create(ip=ip, user=user)
    return obj


def mark_form_render(request, action):
    key = f"form_render_{action}"
    request.session[key] = timezone.now().isoformat()


def _compute_wait_seconds(request, action):
    key = f"form_render_{action}"
    ts = request.session.get(key)
    if not ts:
        return None
    try:
        shown = timezone.datetime.fromisoformat(ts)
        if timezone.is_naive(shown):
            shown = timezone.make_aware(shown, timezone.get_default_timezone())
        delta = timezone.now() - shown
        return max(0, int(delta.total_seconds()))
    except Exception:
        return None


def record_failure(request, action, meta_text="", status_code=400):
    activity = _get_activity(request)
    activity.failure_count = int(activity.failure_count or 0) + 1
    if activity.failure_count >= 3:
        activity.is_tracking = True
    activity.unread = True
    activity.save(update_fields=["failure_count", "is_tracking", "last_seen", "unread"])

    wait_seconds = _compute_wait_seconds(request, action)
    extra = f"{meta_text}"
    if wait_seconds is not None:
        extra = f"{extra} | wait={wait_seconds}s".strip()

    ip = get_client_ip(request) or ""
    user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]
    referer = (request.META.get("HTTP_REFERER") or "")[:512]
    query = (request.META.get("QUERY_STRING") or "")[:512]
    SuspiciousEvent.objects.create(
        activity=activity,
        method=request.method,
        path=request.path[:512],
        query_string=query,
        referer=referer,
        user_agent=user_agent,
        status_code=int(status_code),
        action=action[:64],
        meta=extra[:2048],
    )

    cache_key = f"sus_rate:{ip}"
    window = cache.get(cache_key, [])
    now = timezone.now()
    window = [t for t in window if (now - t).total_seconds() <= 60]
    window.append(now)
    cache.set(cache_key, window, 60)
    if len(window) >= 3:
        activity.is_tracking = True
        activity.unread = True
        activity.save(update_fields=["is_tracking", "last_seen", "unread"])


def record_success(request, action, meta_text="", user=None, status_code=200):
    activity = _get_activity(request)
    if user and not activity.user:
        activity.user = user
    activity.last_success_at = timezone.now()
    activity.unread = True
    activity.save(update_fields=["user", "last_success_at", "unread", "last_seen"])
    if not activity.suppress_logging:
        ip = get_client_ip(request) or ""
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:512]
        referer = (request.META.get("HTTP_REFERER") or "")[:512]
        query = (request.META.get("QUERY_STRING") or "")[:512]
        SuspiciousEvent.objects.create(
            activity=activity,
            method=request.method,
            path=request.path[:512],
            query_string=query,
            referer=referer,
            user_agent=user_agent,
            status_code=int(status_code),
            action=action[:64],
            meta=(meta_text or "")[:2048],
        )
