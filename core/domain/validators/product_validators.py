"""
Domain Layer: Product Validators
اعتبارسنجی‌های محصول
"""
from django.core.exceptions import ValidationError
from typing import Optional


def validate_product_name(name: str) -> None:
    """
    اعتبارسنجی نام محصول
    
    Args:
        name: نام محصول
    
    Raises:
        ValidationError: اگر نام معتبر نباشد
    """
    if not name or len(name.strip()) == 0:
        raise ValidationError("Product name cannot be empty.")
    
    if len(name) > 255:
        raise ValidationError("Product name must be less than 255 characters.")
    
    if len(name) < 2:
        raise ValidationError("Product name must be at least 2 characters.")


def validate_product_price(price) -> None:
    """
    اعتبارسنجی قیمت محصول
    
    Args:
        price: قیمت محصول
    
    Raises:
        ValidationError: اگر قیمت معتبر نباشد
    """
    if price is None:
        raise ValidationError("Product price is required.")
    
    if price <= 0:
        raise ValidationError("Product price must be positive.")


def validate_product_slug(slug: str) -> None:
    """
    اعتبارسنجی slug محصول
    
    Args:
        slug: slug محصول
    
    Raises:
        ValidationError: اگر slug معتبر نباشد
    """
    if not slug or len(slug.strip()) == 0:
        raise ValidationError("Product slug cannot be empty.")
    
    if len(slug) > 100:
        raise ValidationError("Slug must be less than 100 characters.")
    
    import re
    if not re.match(r'^[a-z0-9-]+$', slug):
        raise ValidationError("Slug may contain lowercase letters, digits, and hyphens only.")


def validate_product_discount(original_price, discounted_price) -> None:
    """
    اعتبارسنجی تخفیف محصول
    
    Args:
        original_price: قیمت اصلی
        discounted_price: قیمت تخفیف‌شده
    
    Raises:
        ValidationError: اگر تخفیف معتبر نباشد
    """
    if original_price and discounted_price:
        if original_price < discounted_price:
            raise ValidationError("Original price must be greater than discounted price.")


def validate_product_description(description: Optional[str]) -> None:
    """
    اعتبارسنجی توضیح محصول
    
    Args:
        description: توضیح محصول
    
    Raises:
        ValidationError: اگر توضیح معتبر نباشد
    """
    if description and len(description) > 5000:
        raise ValidationError("Product description must be less than 5000 characters.")
