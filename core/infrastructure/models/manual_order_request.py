from django.db import models
from django.contrib.auth import get_user_model
from core.infrastructure.models.user_location import UserLocation

User = get_user_model()


class ManualOrderRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    reference = models.CharField(max_length=12)
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deliver = models.BooleanField(default=False)

    location = models.ForeignKey(
        UserLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    delivery_slot = models.CharField(max_length=64, blank=True, null=True)
    items_snapshot = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.reference} ({self.status})"