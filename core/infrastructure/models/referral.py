from django.db import models
from django.contrib.auth.models import User


class ReferralRecord(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_owner')
    used_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_used_by')
    created_at = models.DateTimeField(auto_now_add=True)
    has_order = models.BooleanField(default=False)

    class Meta:
        unique_together = ('owner', 'used_by')


class DiscountCode(models.Model):
    code = models.CharField(max_length=12, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_codes')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    expires_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        from django.utils import timezone
        if self.used_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True