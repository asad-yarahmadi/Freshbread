"""
Application Layer: Product Management Service
منطق تجاری برای مدیریت محصولات
"""
import os
import logging
from typing import Dict, Any, List, Optional
from django.core.exceptions import ValidationError

from ...domain.entities.product_entity import ProductEntity
from ...domain.validators.product_validators import (
    validate_product_name,
    validate_product_price,
    validate_product_slug,
    validate_product_discount,
    validate_product_description
)
from ...infrastructure.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductException(Exception):
    """Exception اختصاصی برای خطاهای مدیریت محصول"""
    pass


class ProductValidationException(ProductException):
    """Exception برای خطاهای اعتبارسنجی"""
    pass


class ProductService:
    """
    سرویس مدیریت محصولات
    شامل ایجاد، بروزرسانی، حذف، و جستجو
    """
    
    @classmethod
    def create_product(cls, product_data: Dict[str, Any], images: List = None) -> 'ProductEntity':
        """
        ایجاد محصول جدید
        
        Args:
            product_data: داده‌های محصول (dict)
            images: لیست فایل‌های عکس (اختیاری)
        
        Returns:
            ProductEntity
        
        Raises:
            ProductValidationException: اگر داده‌های معتبر نباشند
            ProductException: خطاهای دیگر
        """
        # اعتبارسنجی داده‌ها
        try:
            validate_product_name(product_data.get('name', ''))
            validate_product_price(product_data.get('price'))
            validate_product_slug(product_data.get('slug', ''))
            validate_product_description(product_data.get('description'))
            
            original_price = product_data.get('original_price')
            price = product_data.get('price')
            if original_price:
                validate_product_discount(original_price, price)
        
        except ValidationError as e:
            raise ProductValidationException(f"Validation error: {e.message}")
        
        # بررسی تکرار slug
        if ProductRepository.product_exists_by_slug(product_data.get('slug', '')):
            raise ProductValidationException("This slug is already in use.")
        
        try:
            # ایجاد محصول در DB
            product = ProductRepository.create_product(product_data)
            
            # اضافه کردن تصاویر
            if images:
                ProductRepository.add_product_images(product, images)
            
            logger.info(f"محصول جدید ایجاد شد: {product.name} (ID: {product.id})")
            
            return cls._product_to_entity(product)
        
        except Exception as e:
            logger.exception(f"Error creating product: {str(e)}")
            raise ProductException(f"Error creating product: {str(e)}")
    
    @classmethod
    def update_product(cls, product_id: int, product_data: Dict[str, Any]) -> 'ProductEntity':
        """
        بروزرسانی محصول
        
        Args:
            product_id: شناسهٔ محصول
            product_data: داده‌های جدید
        
        Returns:
            ProductEntity
        
        Raises:
            ProductException: اگر محصول پیدا نشود یا خطای دیگر
        """
        product = ProductRepository.get_product_by_id(product_id)
        if not product:
            raise ProductException(f"Product with ID {product_id} not found.")
        name_in = product_data.get('name')
        if name_in is not None:
            from ...infrastructure.models import Product as _P
            from django.db.models import Q
            if _P.objects.filter(Q(name=name_in) & ~Q(id=product_id)).exists():
                raise ProductValidationException("This name is already in use by another product.")
        slug_in = product_data.get('slug')
        if slug_in is not None:
            try:
                validate_product_slug(slug_in)
            except ValidationError as e:
                raise ProductValidationException(f"Slug validation error: {e.message}")
            from ...infrastructure.models import Product as _P
            from django.db.models import Q
            if _P.objects.filter(Q(slug=slug_in) & ~Q(id=product_id)).exists():
                raise ProductValidationException("This slug is already in use by another product.")
        
        if 'price' in product_data:
            try:
                validate_product_price(product_data['price'])
            except ValidationError as e:
                raise ProductValidationException(f"Price validation error: {e.message}")
        

        try:
            # بروزرسانی محصول
            product = ProductRepository.update_product(product, product_data)
            
            logger.info(f"محصول بروزرسانی شد: {product.name} (ID: {product.id})")
            
            return cls._product_to_entity(product)
        
        except Exception as e:
            logger.exception(f"Error updating product: {str(e)}")
            raise ProductException(f"Error updating product: {str(e)}")
    
    @classmethod
    def delete_product(cls, product_id: int) -> bool:
        """
        حذف محصول و فایل‌های مرتبط
        
        Args:
            product_id: شناسهٔ محصول
        
        Returns:
            bool: True اگر موفق باشد
        
        Raises:
            ProductException: اگر محصول پیدا نشود یا خطای دیگر
        """
        product = ProductRepository.get_product_by_id(product_id)
        if not product:
            raise ProductException(f"Product with ID {product_id} not found.")
        
        try:
            # حذف تصاویر و فایل‌های مرتبط
            cls._delete_product_files(product)
            
            # حذف محصول از DB
            ProductRepository.delete_product(product)
            
            logger.info(f"محصول حذف شد: {product.name} (ID: {product.id})")
            
            return True
        
        except Exception as e:
            logger.exception(f"Error deleting product: {str(e)}")
            raise ProductException(f"Error deleting product: {str(e)}")
    
    @classmethod
    def get_product(cls, product_id: int) -> Optional['ProductEntity']:
        """
        گرفتن محصول بر اساس ID
        
        Args:
            product_id: شناسهٔ محصول
        
        Returns:
            ProductEntity یا None
        """
        product = ProductRepository.get_product_by_id(product_id)
        if product:
            return cls._product_to_entity(product)
        return None
    
    @classmethod
    def get_product_by_slug(cls, slug: str) -> Optional['ProductEntity']:
        """
        گرفتن محصول بر اساس slug
        
        Args:
            slug: slug محصول
        
        Returns:
            ProductEntity یا None
        """
        product = ProductRepository.get_product_by_slug(slug)
        if product:
            return cls._product_to_entity(product)
        return None
    
    @classmethod
    def get_all_products(cls, available_only: bool = False) -> List['ProductEntity']:
        """
        گرفتن تمام محصولات
        
        Args:
            available_only: فقط محصولات موجود
        
        Returns:
            List[ProductEntity]
        """
        products = ProductRepository.get_all_products(available_only=available_only)
        return [cls._product_to_entity(p) for p in products]
    
    @classmethod
    def mark_available(cls, product_id: int) -> 'ProductEntity':
        """
        علامت‌گذاری محصول به عنوان موجود
        
        Args:
            product_id: شناسهٔ محصول
        
        Returns:
            ProductEntity
        """
        product = ProductRepository.get_product_by_id(product_id)
        if not product:
            raise ProductException(f"❌ محصول با ID {product_id} پیدا نشد.")
        
        return cls.update_product(product_id, {'available': True})
    
    @classmethod
    def mark_unavailable(cls, product_id: int) -> 'ProductEntity':
        """
        علامت‌گذاری محصول به عنوان ناموجود
        
        Args:
            product_id: شناسهٔ محصول
        
        Returns:
            ProductEntity
        """
        product = ProductRepository.get_product_by_id(product_id)
        if not product:
            raise ProductException(f"❌ محصول با ID {product_id} پیدا نشد.")
        
        return cls.update_product(product_id, {'available': False})
    
    @staticmethod
    def _product_to_entity(product) -> ProductEntity:
        """
        تبدیل مدل Product به Entity
        
        Args:
            product: Product model instance
        
        Returns:
            ProductEntity
        """
        return ProductEntity(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description or "",
            price=product.price,
            original_price=product.original_price,
            category=product.category or "",
            available=product.available,
            created_at=product.created_at,
            updated_at=getattr(product, 'updated_at', None)
        )
    
    @staticmethod
    def _delete_product_files(product) -> None:
        """
        حذف فایل‌های فیزیکی محصول و تصاویر
        
        Args:
            product: Product model instance
        """
        # حذف عکس اصلی
        main_field_candidates = ('menu_image', 'image', 'main_image', 'photo', 'thumbnail')
        
        for fname in main_field_candidates:
            filefield = getattr(product, fname, None)
            if filefield and hasattr(filefield, 'path'):
                try:
                    path = filefield.path
                    if path and os.path.isfile(path):
                        os.remove(path)
                        logger.info(f"فایل حذف شد: {path}")
                except Exception as e:
                    logger.warning(f"خطا در حذف فایل {fname}: {str(e)}")
        
        # حذف تصاویر مرتبط
        ProductRepository.delete_product_images(product)
