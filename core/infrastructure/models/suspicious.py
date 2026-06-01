from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SuspiciousActivity(models.Model):
    ip = models.GenericIPAddressField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    failure_count = models.IntegerField(default=0)
    is_tracking = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(blank=True, null=True)
    unread = models.BooleanField(default=True)
    suppress_logging = models.BooleanField(default=False)
    last_success_at = models.DateTimeField(blank=True, null=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["ip"]),
            models.Index(fields=["last_seen"]),
        ]

    def __str__(self):
        who = self.user.username if self.user else self.ip
        return f"{who} failures={self.failure_count} tracking={self.is_tracking}"

    def last_success_event(self):
        return self.events.filter(status_code__gte=200, status_code__lt=400).order_by("-created_at").first()


class SuspiciousEvent(models.Model):
    activity = models.ForeignKey(SuspiciousActivity, on_delete=models.CASCADE, related_name="events")
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=512)
    query_string = models.CharField(max_length=512, blank=True)
    referer = models.CharField(max_length=512, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    status_code = models.IntegerField()
    action = models.CharField(max_length=64, blank=True)
    meta = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.path} [{self.status_code}]"
