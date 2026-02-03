"""
Domain Layer: Order Validators
اعتبارسنجی‌های سفارش‌ها
"""
from typing import List, Dict, Any
from decimal import Decimal


def validate_order_status(status: str) -> None:
    """
    اعتبارسنجی وضعیت سفارش
    
    Args:
        status: وضعیت سفارش
    
    Raises:
        ValueError: اگر وضعیت نامعتبر باشد
    """
    valid_statuses = ['pending', 'processing', 'cooking', 'queued', 'sending', 'ready', 'delivered', 'cancelled']
    if status not in valid_statuses:
        raise ValueError(f"وضعیت سفارش نامعتبر است: {status}")


def validate_order_transition(current_status: str, new_status: str) -> None:
    """
    اعتبارسنجی تغییر وضعیت سفارش
    
    Args:
        current_status: وضعیت فعلی
        new_status: وضعیت جدید
    
    Raises:
        ValueError: اگر تغییر نامعتبر باشد
    """
    valid_transitions = {
        'pending': ['processing', 'cancelled'],
        'processing': ['cooking', 'cancelled'],
        'cooking': ['queued', 'cancelled'],
        'queued': ['sending', 'ready', 'cancelled'],
        'sending': ['delivered', 'cancelled'],
        'ready': ['delivered', 'cancelled'],
        'delivered': [],
        'cancelled': []
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        raise ValueError(f"تغییر وضعیت از {current_status} به {new_status} مجاز نیست")


def validate_order_item_quantity(quantity: int, max_quantity: int = 10) -> None:
    """
    اعتبارسنجی تعداد آیتم سفارش
    
    Args:
        quantity: تعداد
        max_quantity: حداکثر تعداد مجاز
    
    Raises:
        ValueError: اگر تعداد نامعتبر باشد
    """
    if quantity < 1:
        raise ValueError("تعداد باید حداقل 1 باشد")
    if quantity > max_quantity:
        raise ValueError(f"حداکثر تعداد مجاز {max_quantity} است")


def validate_order_total(total: Decimal, min_total: Decimal = Decimal('0.01')) -> None:
    """
    اعتبارسنجی مجموع سفارش
    
    Args:
        total: مجموع قیمت
        min_total: حداقل مجموع
    
    Raises:
        ValueError: اگر مجموع نامعتبر باشد
    """
    if total < min_total:
        raise ValueError(f"مجموع سفارش باید حداقل {min_total} باشد")


def validate_order_data(data: Dict[str, Any]) -> None:
    """
    اعتبارسنجی داده‌های سفارش
    
    Args:
        data: داده‌های سفارش
    
    Raises:
        ValueError: اگر داده‌ها نامعتبر باشند
    """
    required_fields = ['user_id', 'items']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"فیلد {field} الزامی است")
    
    if not isinstance(data['items'], list) or len(data['items']) == 0:
        raise ValueError("سفارش باید حداقل یک آیتم داشته باشد")
    
    # اعتبارسنجی آیتم‌ها
    for item in data['items']:
        if not isinstance(item, dict):
            raise ValueError("هر آیتم باید dictionary باشد")
        
        required_item_fields = ['product_id', 'quantity', 'price']
        for field in required_item_fields:
            if field not in item:
                raise ValueError(f"فیلد {field} در آیتم الزامی است")
        
        validate_order_item_quantity(item['quantity'])
        
        if item['price'] <= 0:
            raise ValueError("قیمت آیتم باید مثبت باشد")


def validate_order_cancellation(order_status: str) -> None:
    """
    اعتبارسنجی امکان لغو سفارش
    
    Args:
        order_status: وضعیت سفارش
    
    Raises:
        ValueError: اگر لغو ممکن نباشد
    """
    non_cancellable_statuses = ['delivered', 'cancelled']
    if order_status in non_cancellable_statuses:
        raise ValueError(f"سفارش با وضعیت {order_status} قابل لغو نیست")