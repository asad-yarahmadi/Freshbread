from django.db import models
from django.contrib.auth.models import User
from .product import Product


class Review(models.Model):
    product = models.ForeignKey(
        Product,
            on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    profile_image = models.ImageField(
        upload_to='reviews/profile/',
        blank=True,
        null=True
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        name = self.first_name or (self.user.username if self.user else "Guest")
        return f"{name} - {self.product.name}"


class ReviewImage(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="reviews/images/%Y/%m/%d/")

    def __str__(self):
        return f"Image for {self.review.first_name}"