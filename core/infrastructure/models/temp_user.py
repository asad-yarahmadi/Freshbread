from django.db import models
from django.utils import timezone

class TempUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    acc_prpo = models.BooleanField(default=False)

    ip = models.GenericIPAddressField(blank=True, null=True)

    verification_code = models.CharField(max_length=20)
    expires_at = models.DateTimeField()

    is_verified = models.BooleanField(default=False)
    failed_attempts = models.PositiveIntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        status = "✅" if self.is_verified else "❌"
        return f"TempUser: {self.username} {status}"
