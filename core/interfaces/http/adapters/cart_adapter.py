"""
Adapter برای تبدیل درخواست‌های HTTP به DTO برای Cart Management
"""
from django.http import HttpRequest
from decimal import Decimal
from typing import Dict, Any, Optional

from core.application.dto.cart_dto import AddToCartDTO, SetQuantityDTO


def extract_add_to_cart_data(request: HttpRequest, product_slug: str, quantity: int = 1) -> AddToCartDTO:
    """
    استخراج داده‌های اضافه کردن به سبد از request

    Args:
        request: HttpRequest
        product_slug: slug محصول
        quantity: تعداد

    Returns:
        AddToCartDTO
    """
    return AddToCartDTO(
        product_slug=product_slug,
        quantity=quantity,
        user_id=request.user.id if request.user.is_authenticated else None
    )


def extract_set_quantity_data(request: HttpRequest, product_slug: str, quantity: int) -> SetQuantityDTO:
    """
    استخراج داده‌های تنظیم تعداد از request

    Args:
        request: HttpRequest
        product_slug: slug محصول
        quantity: تعداد

    Returns:
        SetQuantityDTO
    """
    return SetQuantityDTO(
        product_slug=product_slug,
        quantity=quantity,
        user_id=request.user.id if request.user.is_authenticated else None
    )


def create_cart_response(success: bool, message: str, **kwargs) -> Dict[str, Any]:
    """
    ایجاد پاسخ استاندارد برای عملیات سبد

    Args:
        success: آیا عملیات موفق بوده
        message: پیام پاسخ
        **kwargs: پارامترهای اضافی

    Returns:
        Dict: پاسخ
    """
    response = {
        'success': success,
        'message': message
    }
    response.update(kwargs)
    return response


def format_cart_summary_for_template(cart_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    فرمت کردن خلاصه سبد برای استفاده در template

    Args:
        cart_summary: خلاصه سبد از service

    Returns:
        Dict: داده‌های آماده برای template
    """
    return {
        "cart_items": cart_summary["cart_items"],
        "original_total": cart_summary["original_total"],
        "savings": cart_summary["savings"],
        "total": cart_summary["total"],
    }