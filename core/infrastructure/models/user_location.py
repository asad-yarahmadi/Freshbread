from django.db import models
from django.contrib.auth.models import User


class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="locations")

    receiver_is_user = models.BooleanField(default=True)
    receiver_name = models.CharField(max_length=150, blank=True, null=True)
    receiver_phone = models.CharField(max_length=20, blank=True, null=True)

    address_line = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    house_number = models.CharField(max_length=20)

    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.address_line}"