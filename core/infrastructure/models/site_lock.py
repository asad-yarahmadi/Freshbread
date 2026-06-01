from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime

User = get_user_model()


class SiteLock(models.Model):
    is_locked = models.BooleanField(default=False)
    reason = models.TextField(blank=True, null=True)
    schedule_start = models.DateTimeField(blank=True, null=True)
    schedule_end = models.DateTimeField(blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status = "Locked" if self.is_locked else "Unlocked"
        return f"{status} (from {self.schedule_start} to {self.schedule_end})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def is_effective_lock(self, now=None):
        now = now or timezone.now()
        if self.is_locked:
            return True
        if self.schedule_start and self.schedule_end:
            start = self.schedule_start
            end = self.schedule_end
            if timezone.is_naive(start):
                start = timezone.make_aware(start, timezone.get_default_timezone())
            if timezone.is_naive(end):
                end = timezone.make_aware(end, timezone.get_default_timezone())
            if timezone.is_naive(now):
                now = timezone.make_aware(now, timezone.get_default_timezone())
            return start <= now <= end
        return False
