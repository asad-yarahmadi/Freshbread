from django.db import models
from django.contrib.auth.models import User

class PaymentAudit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    total_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='pending')
    last_reference = models.CharField(max_length=100, blank=True, null=True)
    seen_refs = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} {self.status} {self.total_paid}/{self.total_due}"