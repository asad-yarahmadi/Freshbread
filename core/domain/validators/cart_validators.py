"""
Domain Layer: Cart Validators
اعتبارسنجی‌های سبد خرید
"""
from decimal import Decimal
from typing import Dict, Any


def validate_cart_quantity(quantity: int, max_quantity: int = 5) -> None:
    """
    اعتبارسنجی تعداد آیتم در سبد

    Args:
        quantity: تعداد
        max_quantity: حداکثر تعداد مجاز

    Raises:
        ValueError: اگر تعداد نامعتبر باشد
    """
    if quantity < 0:
        raise ValueError("تعداد نمی‌تواند منفی باشد")
    if quantity > max_quantity:
        raise ValueError(f"حداکثر تعداد مجاز {max_quantity} است")


def validate_product_availability(product_available: bool) -> None:
    """
    اعتبارسنجی موجود بودن محصول

    Args:
        product_available: آیا محصول موجود است

    Raises:
        ValueError: اگر محصول موجود نباشد
    """
    if not product_available:
        raise ValueError("این محصول در حال حاضر موجود نیست")


def validate_cart_item_data(item_data: Dict[str, Any]) -> None:
    """
    اعتبارسنجی داده‌های آیتم سبد

    Args:
        item_data: داده‌های آیتم

    Raises:
        ValueError: اگر داده‌ها نامعتبر باشند
    """
    required_fields = ['product_id', 'product_slug', 'product_name', 'price', 'quantity']
    for field in required_fields:
        if field not in item_data:
            raise ValueError(f"فیلد {field} الزامی است")

    if item_data['price'] <= 0:
        raise ValueError("قیمت باید مثبت باشد")

    validate_cart_quantity(item_data['quantity'])


def validate_session_cart_data(session_cart: Dict[str, Any]) -> None:
    """
    اعتبارسنجی داده‌های سبد session

    Args:
        session_cart: داده‌های سبد session

    Raises:
        ValueError: اگر داده‌ها نامعتبر باشند
    """
    if not isinstance(session_cart, dict):
        raise ValueError("داده‌های سبد session باید dictionary باشد")

    for slug, item in session_cart.items():
        if not isinstance(item, dict):
            raise ValueError(f"آیتم {slug} باید dictionary باشد")

        required_item_fields = ['name', 'price', 'quantity']
        for field in required_item_fields:
            if field not in item:
                raise ValueError(f"فیلد {field} در آیتم {slug} الزامی است")

        if item['price'] <= 0:
            raise ValueError(f"قیمت آیتم {slug} باید مثبت باشد")

        validate_cart_quantity(item['quantity'])