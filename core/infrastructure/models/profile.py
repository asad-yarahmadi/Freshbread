from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    avatar = models.ImageField(
        upload_to='avatars/',
        default='default_avatar.png'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.CharField(max_length=300, blank=True, null=True)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )

    postal_code = models.CharField(max_length=20, blank=True, null=True)

    signup_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    acc_prpo = models.BooleanField(default=True)
    profile_completed = models.BooleanField(default=False)

    admin_note = models.TextField(blank=True, null=True)

    referral_code = models.CharField(max_length=5, unique=True, blank=True, null=True)
    referral_used_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"
