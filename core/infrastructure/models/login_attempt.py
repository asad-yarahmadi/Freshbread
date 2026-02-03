from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class LoginAttempt(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    permanently_blocked = models.BooleanField(default=False)

    def is_blocked(self):
        now = timezone.now()
        if self.permanently_blocked:
            return True
        if self.blocked_until and now < self.blocked_until:
            return True
        return False

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.ip_address} - blocked_until: {self.blocked_until} - permanent: {self.permanently_blocked}"
    