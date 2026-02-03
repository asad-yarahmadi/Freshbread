"""
Application Layer: Review DTOs
انتقال داده‌های نظرات
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReviewDTO:
    """
    DTO برای نمایش نظر
    """
    id: int
    product_id: int
    product_name: str
    product_slug: str
    rating: int
    comment: str
    first_name: str
    last_name: str
    email: str
    approved: bool
    created_at: datetime
    images: List[str] = field(default_factory=list)
    user_id: Optional[int] = None
    username: Optional[str] = None
    
    @classmethod
    def from_model(cls, review) -> 'ReviewDTO':
        """
        ایجاد DTO از مدل Review
        
        Args:
            review: شیء Review
        
        Returns:
            ReviewDTO: DTO نظر
        """
        return cls(
            id=review.id,
            product_id=review.product.id,
            product_name=review.product.name,
            product_slug=review.product.slug,
            rating=review.rating,
            comment=review.comment,
            first_name=review.first_name,
            last_name=review.last_name,
            email=review.email,
            approved=review.is_approved,
            created_at=review.created_at,
            images=[img.image.url for img in review.images.all()],
            user_id=review.user.id if review.user else None,
            username=review.user.username if review.user else None
        )


@dataclass
class ReviewCreateDTO:
    """
    DTO برای ایجاد نظر جدید
    """
    product_slug: str
    rating: int
    comment: str
    first_name: str
    last_name: str
    email: str
    user_id: Optional[int] = None
    
    @classmethod
    def from_request(cls, request_data: Dict[str, Any], product_slug: str) -> 'ReviewCreateDTO':
        """
        ایجاد DTO از داده‌های درخواست
        
        Args:
            request_data: داده‌های POST
            product_slug: slug محصول
        
        Returns:
            ReviewCreateDTO: DTO ایجاد نظر
        """
        return cls(
            product_slug=product_slug,
            rating=int(request_data.get('rating', 5)),
            comment=request_data.get('comment', ''),
            first_name=request_data.get('first_name', ''),
            last_name=request_data.get('last_name', ''),
            email=request_data.get('email', ''),
            user_id=request_data.get('user_id')
        )


@dataclass
class ReviewStatsDTO:
    """
    DTO برای آمار نظرات محصول
    """
    total_reviews: int
    average_rating: float
    rating_distribution: Dict[int, int]
    
    @classmethod
    def from_stats(cls, stats: Dict[str, Any]) -> 'ReviewStatsDTO':
        """
        ایجاد DTO از آمار
        
        Args:
            stats: آمار نظرات
        
        Returns:
            ReviewStatsDTO: DTO آمار
        """
        return cls(
            total_reviews=stats.get('total_reviews', 0),
            average_rating=stats.get('average_rating', 0.0),
            rating_distribution=stats.get('rating_distribution', {})
        )


@dataclass
class ReviewManagementDTO:
    """
    DTO برای مدیریت نظرات
    """
    id: int
    product_name: str
    rating: int
    comment: str
    first_name: str
    last_name: str
    email: str
    approved: bool
    created_at: datetime
    user_id: Optional[int] = None
    username: Optional[str] = None
    images_count: int = 0
    
    @classmethod
    def from_model(cls, review) -> 'ReviewManagementDTO':
        """
        ایجاد DTO از مدل Review برای مدیریت
        
        Args:
            review: شیء Review
        
        Returns:
            ReviewManagementDTO: DTO مدیریت نظر
        """
        return cls(
            id=review.id,
            product_name=review.product.name,
            rating=review.rating,
            comment=review.comment,
            first_name=review.first_name,
            last_name=review.last_name,
            email=review.email,
            approved=review.is_approved,
            created_at=review.created_at,
            user_id=review.user.id if review.user else None,
            username=review.user.username if review.user else None,
            images_count=review.images.count()
        )


@dataclass
class ReviewResponseDTO:
    """
    DTO برای پاسخ عملیات نظرات
    """
    success: bool
    message: str
    review_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_response(cls, message: str, review_id: Optional[int] = None, data: Optional[Dict[str, Any]] = None) -> 'ReviewResponseDTO':
        """
        پاسخ موفق
        
        Args:
            message: پیام
            review_id: شناسه نظر
            data: داده‌های اضافی
        
        Returns:
            ReviewResponseDTO: DTO پاسخ
        """
        return cls(
            success=True,
            message=message,
            review_id=review_id,
            data=data
        )
    
    @classmethod
    def error_response(cls, message: str) -> 'ReviewResponseDTO':
        """
        پاسخ خطا
        
        Args:
            message: پیام خطا
        
        Returns:
            ReviewResponseDTO: DTO پاسخ
        """
        return cls(
            success=False,
            message=message
        )