from django.db import models
from .product import Product
# ✅ Multiple detail images for product
class ProductDetailImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="detail_images")
    image = models.ImageField(upload_to="detail_images/")

    def __str__(self):
        return f"Detail image for {self.product.name}"
