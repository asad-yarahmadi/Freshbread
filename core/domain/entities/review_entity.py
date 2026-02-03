"""
Domain Layer: Review Entities
قوانین تجاری نظرات
"""
from decimal import Decimal
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReviewEntity:
    """
    Entity برای نظر
    """
    id: Optional[int]
    product_id: int
    product_slug: str
    user_id: Optional[int]
    first_name: str
    last_name: str
    email: Optional[str]
    rating: int
    title: str
    comment: str
    is_approved: bool = False
    created_at: Optional[datetime] = None
    images: List[str] = None  # لیست URL تصاویر

    def __post_init__(self):
        """اعتبارسنجی پس از ایجاد"""
        if self.images is None:
            self.images = []
        self.validate_rating()

    def validate_rating(self) -> None:
        """
        اعتبارسنجی امتیاز
        
        Raises:
            ValueError: اگر امتیاز نامعتبر باشد
        """
        if not (1 <= self.rating <= 5):
            raise ValueError("امتیاز باید بین 1 تا 5 باشد")

    def get_full_name(self) -> str:
        """
        گرفتن نام کامل
        
        Returns:
            str: نام کامل
        """
        return f"{self.first_name} {self.last_name}".strip()

    def approve(self) -> None:
        """
        تأیید نظر
        """
        self.is_approved = True

    def reject(self) -> None:
        """
        رد نظر
        """
        self.is_approved = False

    def has_images(self) -> bool:
        """
        بررسی داشتن تصویر
        
        Returns:
            bool
        """
        return len(self.images) > 0

    def get_rating_stars(self) -> str:
        """
        گرفتن نمایش ستاره‌ای امتیاز
        
        Returns:
            str: نمایش ستاره‌ای
        """
        return "★" * self.rating + "☆" * (5 - self.rating)

    def is_recent(self, days: int = 30) -> bool:
        """
        بررسی اینکه نظر اخیر است
        
        Args:
            days: تعداد روزها
        
        Returns:
            bool
        """
        if not self.created_at:
            return False
        from datetime import timedelta
        return (datetime.now() - self.created_at) <= timedelta(days=days)