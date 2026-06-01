from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import render
from core.application.security.ddos_checker import ddos_checker
from core.infrastructure.models import SiteLock, SuspiciousActivity, SuspiciousEvent
from core.interfaces.http.utils.ip import get_client_ip


class SiteSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = (request.path or "").lower()
        if path.startswith("/static/") or path.startswith("/media/"):
            return self.get_response(request)

        ip = get_client_ip(request) or "0.0.0.0"
        try:
            user = getattr(request, "user", None)
            if user and getattr(user, "is_authenticated", False):
                SuspiciousActivity.objects.filter(ip=ip, user__isnull=True).update(user=user)
        except Exception:
            pass
        blocked_flag = cache.get(f"ip_blocked:{ip}")
        if blocked_flag is None:
            blocked = SuspiciousActivity.objects.filter(ip=ip, is_blocked=True).first()
            if blocked and (not blocked.blocked_until or timezone.now() <= blocked.blocked_until):
                cache.set(f"ip_blocked:{ip}", True, 60)
                blocked_flag = True
            else:
                cache.set(f"ip_blocked:{ip}", False, 60)
                blocked_flag = False
        if blocked_flag:
            self._track(request, 403)
            raise PermissionDenied("IP blocked")

        blocked = ddos_checker.check(request)
        if blocked is not None:
            self._track(request, 403)
            return blocked

        now = timezone.now()
        lock_state = cache.get("site_lock_state")
        if lock_state is None:
            site_lock = SiteLock.get_solo()
            is_locked = site_lock.is_effective_lock(now=now)
            reason = site_lock.reason or ""
            lock_state = {"is_locked": is_locked, "reason": reason}
            cache.set("site_lock_state", lock_state, 60)

        ddos_lock = cache.get("site_locked", False)
        is_locked = lock_state.get("is_locked") or bool(ddos_lock)

        if is_locked:
            user = getattr(request, "user", None)
            if path.startswith("/admin_adminali_admin/"):
                return self.get_response(request)
            if not (user and (user.is_staff or user.is_superuser)):
                self._track(request, 403)
                raise PermissionDenied("Site locked")

        response = self.get_response(request)
        self._track(request, getattr(response, "status_code", 200))
        return response

    def _track(self, request, status_code):
        try:
            ip = get_client_ip(request) or "0.0.0.0"
            user = getattr(request, "user", None)
            activity = SuspiciousActivity.objects.filter(ip=ip, user=user if getattr(user, "is_authenticated", False) else None).first()
            if not activity:
                activity = SuspiciousActivity.objects.create(ip=ip, user=user if getattr(user, "is_authenticated", False) else None)
            fail_codes = {400, 401, 403, 429, 500, 502, 503}
            if status_code in fail_codes:
                activity.failure_count = int(activity.failure_count or 0) + 1
                if activity.failure_count >= 3:
                    activity.is_tracking = True
                activity.save(update_fields=["failure_count", "is_tracking", "last_seen"])
            if activity.is_tracking:
                if activity.events.count() >= 100:
                    oldest = activity.events.order_by("created_at").first()
                    if oldest:
                        oldest.delete()
                if not activity.suppress_logging:
                    SuspiciousEvent.objects.create(
                        activity=activity,
                        method=request.method,
                        path=request.path[:512],
                        query_string=(request.META.get("QUERY_STRING") or "")[:512],
                        referer=(request.META.get("HTTP_REFERER") or "")[:512],
                        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:512],
                        status_code=int(status_code),
                    )
                if 200 <= int(status_code) < 400:
                    activity.last_success_at = timezone.now()
                    activity.unread = True
                    activity.save(update_fields=["last_success_at", "unread", "last_seen"])
        except Exception:
            pass
    def _build_ctx(self, request):
        reason = cache.get("site_lock_reason") or ""
        sched = cache.get("site_lock_schedule") or {}
        start = sched.get("start")
        end = sched.get("end")
        
        return {
            "reason": reason,
            "start": start,
            "end": end,
            
        }