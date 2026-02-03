from django.db import models
from django.contrib.auth.models import User

class SocialProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    provider = models.CharField(max_length=50, default='google')  # google, github, etc.
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_completed = models.BooleanField(default=False)
    google_login_count = models.IntegerField(default=0)
    acc_prpo = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    # 🗺️ New location fields:

    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    class Meta:
        unique_together = ("email", "provider")

    def __str__(self):
        return f"{self.email} ({self.provider})"
