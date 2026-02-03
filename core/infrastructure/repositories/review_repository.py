"""
Infrastructure Layer: Review Repository
دسترسی به مدل Review
"""
from typing import List, Optional, Dict, Any
from django.db.models import Avg, Count

from core.infrastructure.models import Review, ReviewImage


class ReviewRepository:
    """
    Repository برای مدیریت دسترسی به نظرات
    """

    @staticmethod
    def get_reviews_for_product(product_id: int, approved_only: bool = True) -> List[Review]:
        """
        گرفتن نظرات محصول
        
        Args:
            product_id: شناسه محصول
            approved_only: فقط نظرات تأیید شده
        
        Returns:
            List[Review]: لیست نظرات
        """
        queryset = Review.objects.filter(product_id=product_id)
        if approved_only:
            queryset = queryset.filter(is_approved=True)
        return list(queryset.order_by('-created_at'))

    @staticmethod
    def get_review_by_id(review_id: int) -> Optional[Review]:
        """
        گرفتن نظر بر اساس شناسه
        
        Args:
            review_id: شناسه نظر
        
        Returns:
            Review یا None
        """
        try:
            return Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return None

    @staticmethod
    def create_review(review_data: Dict[str, Any], images: List[Any] = None) -> Review:
        """
        ایجاد نظر جدید
        
        Args:
            review_data: داده‌های نظر
            images: لیست تصاویر
        
        Returns:
            Review: نظر ایجاد شده
        """
        review = Review.objects.create(**review_data)
        
        # ذخیره تصاویر
        if images:
            for image in images:
                ReviewImage.objects.create(review=review, image=image)
        
        return review

    @staticmethod
    def update_review(review: Review, update_data: Dict[str, Any]) -> Review:
        """
        بروزرسانی نظر
        
        Args:
            review: شیء Review
            update_data: داده‌های بروزرسانی
        
        Returns:
            Review: نظر بروزرسانی شده
        """
        for key, value in update_data.items():
            setattr(review, key, value)
        review.save()
        return review

    @staticmethod
    def delete_review(review: Review) -> None:
        """
        حذف نظر
        
        Args:
            review: شیء Review
        """
        review.delete()

    @staticmethod
    def approve_review(review: Review) -> Review:
        """
        تأیید نظر
        
        Args:
            review: شیء Review
        
        Returns:
            Review: نظر تأیید شده
        """
        review.is_approved = True
        review.save(update_fields=['is_approved'])
        return review

    @staticmethod
    def reject_review(review: Review) -> Review:
        """
        رد نظر
        
        Args:
            review: شیء Review
        
        Returns:
            Review: نظر رد شده
        """
        review.is_approved = False
        review.save(update_fields=['is_approved'])
        return review

    @staticmethod
    def get_product_rating_stats(product_id: int) -> Dict[str, Any]:
        """
        گرفتن آمار امتیاز محصول
        
        Args:
            product_id: شناسه محصول
        
        Returns:
            Dict: آمار امتیاز
        """
        stats = Review.objects.filter(
            product_id=product_id,
            is_approved=True
        ).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        return {
            'average_rating': round(stats['avg_rating'] or 0, 1),
            'total_reviews': stats['total_reviews'] or 0
        }

    @staticmethod
    def get_all_reviews(approved_only: bool = False) -> List[Review]:
        """
        گرفتن تمام نظرات
        
        Args:
            approved_only: فقط نظرات تأیید شده
        
        Returns:
            List[Review]: لیست نظرات
        """
        queryset = Review.objects.all()
        if approved_only:
            queryset = queryset.filter(is_approved=True)
        return list(queryset.order_by('-created_at').prefetch_related('images'))

    @staticmethod
    def get_reviews_by_user(user_id: int) -> List[Review]:
        """
        گرفتن نظرات کاربر
        
        Args:
            user_id: شناسه کاربر
        
        Returns:
            List[Review]: لیست نظرات
        """
        return list(
            Review.objects.filter(user_id=user_id)
            .order_by('-created_at')
            .prefetch_related('images')
        )

    @staticmethod
    def ban_user_reviews(user_id: int) -> int:
        """
        غیرفعال کردن تمام نظرات کاربر (برای ban)
        
        Args:
            user_id: شناسه کاربر
        
        Returns:
            int: تعداد نظرات غیرفعال شده
        """
        return Review.objects.filter(user_id=user_id).update(is_approved=False)

    @staticmethod
    def get_pending_reviews() -> List[Review]:
        """
        گرفتن نظرات در انتظار تأیید
        
        Returns:
            List[Review]: لیست نظرات
        """
        return list(
            Review.objects.filter(is_approved=False)
            .order_by('-created_at')
            .prefetch_related('images')
        )