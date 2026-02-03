"""
Domain Layer: Cart Entities
قوانین تجاری سبد خرید
"""
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CartItemEntity:
    """
    Entity برای آیتم سبد خرید
    """
    product_id: int
    product_slug: str
    product_name: str
    price: Decimal
    original_price: Optional[Decimal]
    quantity: int
    max_quantity: int = 5

    def __post_init__(self):
        """اعتبارسنجی پس از ایجاد"""
        self.validate_quantity()

    def validate_quantity(self) -> None:
        """
        اعتبارسنجی تعداد

        Raises:
            ValueError: اگر تعداد نامعتبر باشد
        """
        if self.quantity < 0:
            raise ValueError("تعداد نمی‌تواند منفی باشد")
        if self.quantity > self.max_quantity:
            raise ValueError(f"حداکثر تعداد مجاز {self.max_quantity} است")

    def get_total_price(self) -> Decimal:
        """
        محاسبه قیمت کل آیتم

        Returns:
            Decimal: قیمت کل
        """
        return self.price * self.quantity

    def get_original_total_price(self) -> Decimal:
        """
        محاسبه قیمت کل اصلی (قبل از تخفیف)

        Returns:
            Decimal: قیمت کل اصلی
        """
        original_price = self.original_price or self.price
        return original_price * self.quantity

    def get_savings(self) -> Decimal:
        """
        محاسبه صرفه‌جویی

        Returns:
            Decimal: مبلغ صرفه‌جویی
        """
        return self.get_original_total_price() - self.get_total_price()

    def has_discount(self) -> bool:
        """
        بررسی اینکه آیا محصول تخفیف دارد

        Returns:
            bool
        """
        return self.original_price is not None and self.original_price > self.price

    def increase_quantity(self, amount: int = 1) -> None:
        """
        افزایش تعداد

        Args:
            amount: مقدار افزایش

        Raises:
            ValueError: اگر تعداد بیش از حد شود
        """
        new_quantity = self.quantity + amount
        if new_quantity > self.max_quantity:
            new_quantity = self.max_quantity
        self.quantity = new_quantity
        self.validate_quantity()

    def decrease_quantity(self, amount: int = 1) -> None:
        """
        کاهش تعداد

        Args:
            amount: مقدار کاهش

        Raises:
            ValueError: اگر تعداد منفی شود
        """
        new_quantity = self.quantity - amount
        if new_quantity < 0:
            new_quantity = 0
        self.quantity = new_quantity
        self.validate_quantity()

    def set_quantity(self, quantity: int) -> None:
        """
        تنظیم تعداد

        Args:
            quantity: تعداد جدید

        Raises:
            ValueError: اگر تعداد نامعتبر باشد
        """
        self.quantity = quantity
        self.validate_quantity()


@dataclass
class CartEntity:
    """
    Entity برای سبد خرید
    """
    user_id: Optional[int]
    items: List[CartItemEntity]
    is_authenticated: bool = False

    def __post_init__(self):
        """اعتبارسنجی پس از ایجاد"""
        if self.items is None:
            self.items = []

    def add_item(self, item: CartItemEntity) -> None:
        """
        اضافه کردن آیتم به سبد

        Args:
            item: آیتم جدید
        """
        # بررسی اینکه آیا محصول قبلاً در سبد وجود دارد
        existing_item = self.get_item_by_product_id(item.product_id)
        if existing_item:
            existing_item.increase_quantity(item.quantity)
        else:
            self.items.append(item)

    def remove_item(self, product_id: int) -> bool:
        """
        حذف آیتم از سبد

        Args:
            product_id: شناسه محصول

        Returns:
            bool: True اگر آیتم حذف شد
        """
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                self.items.pop(i)
                return True
        return False

    def get_item_by_product_id(self, product_id: int) -> Optional[CartItemEntity]:
        """
        گرفتن آیتم بر اساس شناسه محصول

        Args:
            product_id: شناسه محصول

        Returns:
            CartItemEntity یا None
        """
        for item in self.items:
            if item.product_id == product_id:
                return item
        return None

    def get_item_by_slug(self, slug: str) -> Optional[CartItemEntity]:
        """
        گرفتن آیتم بر اساس slug محصول

        Args:
            slug: slug محصول

        Returns:
            CartItemEntity یا None
        """
        for item in self.items:
            if item.product_slug == slug:
                return item
        return None

    def get_total_items_count(self) -> int:
        """
        گرفتن تعداد کل آیتم‌ها

        Returns:
            int: تعداد کل آیتم‌ها
        """
        return sum(item.quantity for item in self.items)

    def get_total_price(self) -> Decimal:
        """
        محاسبه قیمت کل سبد (بعد از تخفیف)

        Returns:
            Decimal: قیمت کل
        """
        return sum(item.get_total_price() for item in self.items)

    def get_original_total_price(self) -> Decimal:
        """
        محاسبه قیمت کل اصلی سبد (قبل از تخفیف)

        Returns:
            Decimal: قیمت کل اصلی
        """
        return sum(item.get_original_total_price() for item in self.items)

    def get_total_savings(self) -> Decimal:
        """
        محاسبه کل صرفه‌جویی

        Returns:
            Decimal: مبلغ کل صرفه‌جویی
        """
        savings = self.get_original_total_price() - self.get_total_price()
        return max(Decimal('0.0'), savings)

    def is_empty(self) -> bool:
        """
        بررسی اینکه سبد خالی است

        Returns:
            bool
        """
        return len(self.items) == 0

    def clear(self) -> None:
        """
        پاک کردن سبد
        """
        self.items.clear()

    def merge_with_session_cart(self, session_cart: Dict) -> None:
        """
        ادغام سبد session با سبد فعلی

        Args:
            session_cart: سبد session
        """
        # این منطق باید در service پیاده‌سازی شود
        pass

    def to_dict(self) -> Dict:
        """
        تبدیل به dictionary برای ذخیره در session

        Returns:
            Dict: داده‌های سبد برای session
        """
        return {
            item.product_slug: {
                'name': item.product_name,
                'price': float(item.price),
                'quantity': item.quantity
            }
            for item in self.items
        }