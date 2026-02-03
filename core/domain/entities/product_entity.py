"""
Domain Layer: Product Entity و Business Rules
قوانین تجاری مرتبط با محصول
"""
from decimal import Decimal
from typing import Optional
from datetime import datetime


class ProductEntity:
    """
    Entity برای محصول - شامل قوانین تجاری
    """
    
    def __init__(
        self,
        id: Optional[int],
        name: str,
        slug: str,
        description: str,
        price: Decimal,
        original_price: Optional[Decimal] = None,
        category: str = "",
        available: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.price = price
        self.original_price = original_price
        self.category = category
        self.available = available
        self.created_at = created_at
        self.updated_at = updated_at
    
    def calculate_discount_percentage(self) -> float:
        """
        محاسبه درصد تخفیف
        
        Returns:
            float: درصد تخفیف (0-100)
        """
        if not self.original_price or self.original_price <= 0:
            return 0.0
        
        discount = (self.original_price - self.price) / self.original_price * 100
        return max(0.0, min(100.0, discount))  # between 0-100
    
    def has_discount(self) -> bool:
        """
        بررسی اینکه محصول تخفیف دارد
        
        Returns:
            bool
        """
        return self.original_price is not None and self.original_price > self.price
    
    def get_discounted_price(self) -> Decimal:
        """
        گرفتن قیمت نهایی (بعد از تخفیف)
        
        Returns:
            Decimal
        """
        return self.price
    
    def get_savings_amount(self) -> Decimal:
        """
        محاسبه مبلغ صرفه‌جویی
        
        Returns:
            Decimal
        """
        if not self.original_price:
            return Decimal('0.0')
        return self.original_price - self.price
    
    def is_valid_for_creation(self) -> bool:
        """
        بررسی اینکه محصول برای ایجاد معتبر است
        
        Returns:
            bool
        """
        return (
            self.name and len(self.name) > 0 and
            self.price and self.price > 0 and
            self.slug and len(self.slug) > 0
        )
    
    def is_valid_for_update(self) -> bool:
        """
        بررسی اینکه محصول برای بروزرسانی معتبر است
        
        Returns:
            bool
        """
        return self.is_valid_for_creation() and self.id is not None
    
    def mark_unavailable(self) -> None:
        """
        علامت‌گذاری محصول به عنوان ناموجود
        """
        self.available = False
    
    def mark_available(self) -> None:
        """
        علامت‌گذاری محصول به عنوان موجود
        """
        self.available = True
    
    def __repr__(self) -> str:
        return f"ProductEntity(id={self.id}, name='{self.name}', price={self.price})"
