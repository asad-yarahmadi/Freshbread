from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .product import Product
import uuid
from core.infrastructure.models.user_location import UserLocation

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('processing', 'Processing'),
        ('cooking', 'Cooking'),
        ('queued', 'In Sending Line'),
        ('sending', 'Sending'),
        ('ready', 'Ready to Send'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_code = models.CharField(max_length=12, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deliver = models.BooleanField(default=False)
    delivery_location = models.ForeignKey(
    UserLocation,
    on_delete=models.SET_NULL,
    null=True,
    blank=True
    )
    delivery_slot = models.CharField(max_length=64, blank=True, null=True)
    delivery_code = models.CharField(max_length=12, blank=True, null=True)
    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        return total if total else 0

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if not self.order_code:
            self.order_code = uuid.uuid4().hex[:10].upper()
        if self.status == 'delivered' and not self.completed_at:
            self.completed_at = timezone.now()
        if not creating:
            self.total_price = self.calculate_total()
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.order_code} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super(OrderItem, self).save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"