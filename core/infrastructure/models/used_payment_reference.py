from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UsedPaymentReference(models.Model):
    reference = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} - {self.amount}"
