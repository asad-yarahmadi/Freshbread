"""
Application Layer: Review Service
منطق تجاری نظرات
"""
import logging
from typing import List, Dict, Any, Optional

from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile

from ...domain.entities.review_entity import ReviewEntity
from ...domain.validators.review_validators import (
    validate_review_data,
    validate_image_files
)
from ...infrastructure.repositories.review_repository import ReviewRepository
from ...infrastructure.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class ReviewException(Exception):
    """Exception اختصاصی برای خطاهای نظرات"""
    pass


class ReviewValidationException(ReviewException):
    """Exception برای خطاهای اعتبارسنجی نظر"""
    pass


class ReviewService:
    """
    سرویس مدیریت نظرات
    شامل ایجاد، تأیید، رد و مدیریت نظرات
    """

    @classmethod
    def create_review(
        cls,
        product_slug: str,
        review_data: Dict[str, Any],
        images: List[UploadedFile] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        ایجاد نظر جدید
        
        Args:
            product_slug: slug محصول
            review_data: داده‌های نظر
            images: لیست تصاویر
            user: کاربر (اختیاری)
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            ReviewValidationException: خطاهای اعتبارسنجی
            ReviewException: خطاهای دیگر
        """
        try:
            # گرفتن محصول
            product = ProductRepository.get_product_by_slug(product_slug)
            if not product:
                raise ReviewException(f"Product with slug {product_slug} not found")
            
            # آماده‌سازی داده‌ها
            review_data['product'] = product
            
            if user and user.is_authenticated:
                review_data['user'] = user
                review_data['first_name'] = user.first_name or user.username
                review_data['last_name'] = user.last_name or ""
            
            # اعتبارسنجی داده‌ها
            validate_review_data(review_data)
            
            # اعتبارسنجی تصاویر
            if images:
                validate_image_files(images)
            
            # ایجاد نظر
            review = ReviewRepository.create_review(review_data, images)
            
            logger.info(f"New review created for product {product.name}")
            
            return {
                'success': True,
                'review_id': review.id,
                'message': 'Your review was submitted and will appear after approval'
            }
            
        except Exception as e:
            logger.exception(f"Error creating review: {str(e)}")
            raise ReviewException(f"Error creating review: {str(e)}")

    @classmethod
    def get_product_reviews(cls, product_slug: str, approved_only: bool = True) -> Dict[str, Any]:
        """
        گرفتن نظرات محصول
        
        Args:
            product_slug: slug محصول
            approved_only: فقط نظرات تأیید شده
        
        Returns:
            Dict: نظرات و آمار
        """
        try:
            product = ProductRepository.get_product_by_slug(product_slug)
            if not product:
                raise ReviewException(f"Product with slug {product_slug} not found")
            
            reviews = ReviewRepository.get_reviews_for_product(product.id, approved_only)
            stats = ReviewRepository.get_product_rating_stats(product.id)
            
            return {
                'product': product,
                'reviews': reviews,
                'stats': stats
            }
            
        except Exception as e:
            logger.exception(f"Error fetching product reviews: {str(e)}")
            raise ReviewException(f"Error fetching product reviews: {str(e)}")

    @classmethod
    def approve_review(cls, review_id: int) -> Dict[str, Any]:
        """
        تأیید نظر
        
        Args:
            review_id: شناسه نظر
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            ReviewException: اگر نظر پیدا نشود
        """
        try:
            review = ReviewRepository.get_review_by_id(review_id)
            if not review:
                raise ReviewException(f"Review with id {review_id} not found")
            
            ReviewRepository.approve_review(review)
            
            logger.info(f"Review {review_id} approved")
            
            return {
                'success': True,
                'message': f'Review by {review.first_name} approved'
            }
            
        except Exception as e:
            logger.exception(f"Error approving review: {str(e)}")
            raise ReviewException(f"Error approving review: {str(e)}")

    @classmethod
    def reject_review(cls, review_id: int) -> Dict[str, Any]:
        """
        رد نظر
        
        Args:
            review_id: شناسه نظر
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            ReviewException: اگر نظر پیدا نشود
        """
        try:
            review = ReviewRepository.get_review_by_id(review_id)
            if not review:
                raise ReviewException(f"Review with id {review_id} not found")
            
            ReviewRepository.reject_review(review)
            
            logger.info(f"Review {review_id} rejected")
            
            return {
                'success': True,
                'message': f'Review by {review.first_name} rejected'
            }
            
        except Exception as e:
            logger.exception(f"Error rejecting review: {str(e)}")
            raise ReviewException(f"Error rejecting review: {str(e)}")

    @classmethod
    def delete_review(cls, review_id: int, user: Optional[User] = None) -> Dict[str, Any]:
        """
        حذف نظر
        
        Args:
            review_id: شناسه نظر
            user: کاربر (برای بررسی دسترسی)
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            ReviewException: اگر نظر پیدا نشود یا دسترسی مجاز نباشد
        """
        try:
            review = ReviewRepository.get_review_by_id(review_id)
            if not review:
                raise ReviewException(f"Review with id {review_id} not found")
            
            # بررسی دسترسی
            if user and not user.is_staff:
                if review.user != user:
                    raise ReviewException("You are not allowed to delete this review")
            
            product_name = review.product.name
            ReviewRepository.delete_review(review)
            
            logger.info(f"Review {review_id} deleted")
            
            return {
                'success': True,
                'message': 'Review deleted'
            }
            
        except Exception as e:
            logger.exception(f"Error deleting review: {str(e)}")
            raise ReviewException(f"Error deleting review: {str(e)}")

    @classmethod
    def ban_user_from_reviews(cls, review_id: int) -> Dict[str, Any]:
        """
        مسدود کردن کاربر از نظر دادن
        
        Args:
            review_id: شناسه نظر
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            ReviewException: اگر نظر پیدا نشود
        """
        try:
            review = ReviewRepository.get_review_by_id(review_id)
            if not review:
                raise ReviewException(f"Review with id {review_id} not found")
            
            if not review.user:
                raise ReviewException("This review was submitted by a guest user")
            
            # غیرفعال کردن تمام نظرات کاربر
            banned_count = ReviewRepository.ban_user_reviews(review.user.id)
            
            # غیرفعال کردن کاربر
            review.user.is_active = False
            review.user.save(update_fields=['is_active'])
            
            logger.warning(f"User {review.user.username} banned from reviews")
            
            return {
                'success': True,
                'message': f'User {review.user.username} banned and {banned_count} reviews disabled'
            }
            
        except Exception as e:
            logger.exception(f"Error banning user: {str(e)}")
            raise ReviewException(f"Error banning user: {str(e)}")

    @classmethod
    def get_all_reviews(cls, approved_only: bool = False) -> List[Any]:
        """
        گرفتن تمام نظرات برای مدیریت
        
        Args:
            approved_only: فقط نظرات تأیید شده
        
        Returns:
            List: لیست نظرات
        """
        try:
            return ReviewRepository.get_all_reviews(approved_only)
        except Exception as e:
            logger.exception(f"Error fetching all reviews: {str(e)}")
            raise ReviewException(f"Error fetching all reviews: {str(e)}")

    @classmethod
    def get_pending_reviews(cls) -> List[Any]:
        """
        گرفتن نظرات در انتظار تأیید
        
        Returns:
            List: لیست نظرات
        """
        try:
            return ReviewRepository.get_pending_reviews()
        except Exception as e:
            logger.exception(f"Error fetching pending reviews: {str(e)}")
            raise ReviewException(f"Error fetching pending reviews: {str(e)}")

    @classmethod
    def get_user_reviews(cls, user: User) -> List[Any]:
        """
        گرفتن نظرات کاربر
        
        Args:
            user: شیء User
        
        Returns:
            List: لیست نظرات
        """
        try:
            return ReviewRepository.get_reviews_by_user(user.id)
        except Exception as e:
            logger.exception(f"Error fetching user reviews: {str(e)}")
            raise ReviewException(f"Error fetching user reviews: {str(e)}")