"""
Data Transfer Objects برای Product Management
"""
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal


@dataclass
class CreateProductDTO:
    """
    DTO برای ایجاد محصول جدید
    """
    name: str
    slug: str
    description: Optional[str] = None
    price: Decimal = Decimal('0.0')
    original_price: Optional[Decimal] = None
    category: Optional[str] = None
    available: bool = True
    images: Optional[List] = None


@dataclass
class UpdateProductDTO:
    """
    DTO برای بروزرسانی محصول
    """
    product_id: int
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    category: Optional[str] = None
    available: Optional[bool] = None


@dataclass
class ProductResponseDTO:
    """
    DTO برای پاسخ محصول (خروجی)
    """
    id: int
    name: str
    slug: str
    description: str
    price: Decimal
    original_price: Optional[Decimal]
    category: str
    available: bool
    discount_percentage: float = 0.0
    has_discount: bool = False
