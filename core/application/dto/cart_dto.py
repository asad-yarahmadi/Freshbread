"""
Data Transfer Objects برای Cart Management
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from decimal import Decimal


@dataclass
class AddToCartDTO:
    """
    DTO برای اضافه کردن به سبد
    """
    product_slug: str
    quantity: int = 1
    user_id: Optional[int] = None


@dataclass
class CartItemDTO:
    """
    DTO برای آیتم سبد
    """
    product_id: int
    product_slug: str
    product_name: str
    price: Decimal
    original_price: Optional[Decimal]
    quantity: int
    total_price: Decimal = Decimal('0.0')
    savings: Decimal = Decimal('0.0')


@dataclass
class CartSummaryDTO:
    """
    DTO برای خلاصه سبد
    """
    items: List[CartItemDTO]
    total: Decimal = Decimal('0.0')
    original_total: Decimal = Decimal('0.0')
    savings: Decimal = Decimal('0.0')
    total_items: int = 0


@dataclass
class SetQuantityDTO:
    """
    DTO برای تنظیم تعداد
    """
    product_slug: str
    quantity: int
    user_id: Optional[int] = None


@dataclass
class CartResponseDTO:
    """
    DTO برای پاسخ عملیات سبد
    """
    success: bool
    message: str
    quantity: Optional[int] = None
    total: Optional[float] = None
    original_total: Optional[float] = None
    savings: Optional[float] = None