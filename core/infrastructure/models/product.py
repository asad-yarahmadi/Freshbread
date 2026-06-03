from django.db import models
from django.utils.text import slugify


class CategorySort(models.Model):
    CATEGORY_CHOICES = [
        ('iranianfood', 'Iranian food'),
        ('fastfood', 'Fast Food'),
        ('bread', 'Bread'),
        ('pastries', 'Pastries'),
        ('cake', 'Cakes'),
        ('appetizer', 'Appetizer'),
        ('dessert', 'Dessert'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.get_category_display()} - Order {self.sort_order}"


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('iranianfood', 'Iranian food'),
        ('fastfood', 'Fast Food'),
        ('bread', 'Bread'),
        ('pastries', 'Pastries'),
        ('cake', 'Cakes'),
        ('appetizer', 'Appetizer'),
        ('dessert', 'Dessert'),
    ]

    # نام و توضیحات
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=800)

    # قیمت اصلی قبل از تخفیف
    original_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price before discount"
    )

    # قیمت نهایی (بعد از تخفیف)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Final price after discount"
    )

    # عکس منو
    menu_image = models.ImageField(upload_to='menu_images/', default='default_food.jpg')

    # دسته‌بندی
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='slowfood')

    # وضعیت موجودی
    available = models.BooleanField(default=True)

    # Sort Order for individual products
    sort_order = models.IntegerField(default=0)

    # تاریخ ایجاد
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    # درصد تخفیف محاسبه‌شده
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0

    # قیمت نهایی
    def final_price(self):
        return self.price
