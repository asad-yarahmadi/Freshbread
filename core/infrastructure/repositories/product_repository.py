"""
Infrastructure Layer: Product Repository
دسترسی به مدل Product و عملیات DB
"""
from typing import Optional, List, Dict, Any
from django.core.paginator import Paginator, Page
from decimal import Decimal

from core.infrastructure.models import Product, ProductDetailImage


class ProductRepository:
    """
    Repository برای مدیریت دسترسی به مدل Product
    """
    
    DEFAULT_PAGE_SIZE = 20
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """
        گرفتن محصول بر اساس ID
        
        Args:
            product_id: شناسهٔ محصول
        
        Returns:
            Product یا None
        """
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Product]:
        """
        گرفتن محصول بر اساس slug
        
        Args:
            slug: slug محصول
        
        Returns:
            Product یا None
        """
        try:
            return Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_products(available_only: bool = False, order_by: str = '-created_at') -> List[Product]:
        """
        گرفتن تمام محصولات
        
        Args:
            available_only: فقط محصولات موجود
            order_by: ترتیب نمایش
        
        Returns:
            List[Product]
        """
        qs = Product.objects.all()
        
        if available_only:
            qs = qs.filter(available=True)
        
        return list(qs.order_by(order_by))
    
    @staticmethod
    def get_products_paginated(page: int = 1, page_size: int = None, available_only: bool = False) -> Page:
        """
        گرفتن محصولات با pagination
        
        Args:
            page: شماره صفحه
            page_size: تعداد موارد در هر صفحه
            available_only: فقط محصولات موجود
        
        Returns:
            Page object
        """
        if page_size is None:
            page_size = ProductRepository.DEFAULT_PAGE_SIZE
        
        qs = Product.objects.all()
        
        if available_only:
            qs = qs.filter(available=True)
        
        qs = qs.order_by('-created_at')
        
        paginator = Paginator(qs, page_size)
        return paginator.get_page(page)
    
    @staticmethod
    def get_products_by_category(category: str) -> List[Product]:
        """
        گرفتن محصولات بر اساس دسته‌بندی
        
        Args:
            category: نام دسته‌بندی
        
        Returns:
            List[Product]
        """
        return list(
            Product.objects.filter(category=category)
            .filter(available=True)
            .order_by('-created_at')
        )
    
    @staticmethod
    def create_product(data: Dict[str, Any]) -> Product:
        """
        ایجاد محصول جدید
        
        Args:
            data: داده‌های محصول (dict)
        
        Returns:
            Product
        """
        product = Product.objects.create(**data)
        return product
    
    @staticmethod
    def update_product(product: Product, data: Dict[str, Any]) -> Product:
        """
        بروزرسانی محصول
        
        Args:
            product: شیء Product
            data: داده‌های جدید
        
        Returns:
            Product
        """
        for field, value in data.items():
            setattr(product, field, value)
        product.save()
        return product
    
    @staticmethod
    def delete_product(product: Product) -> None:
        """
        حذف محصول و تصاویر مرتبط
        
        Args:
            product: شیء Product
        """
        # حذف تصاویر مرتبط
        ProductDetailImage.objects.filter(product=product).delete()
        
        # حذف محصول
        product.delete()
    
    @staticmethod
    def delete_product_images(product: Product) -> None:
        """
        حذف تمام تصاویر محصول
        
        Args:
            product: شیء Product
        """
        images = ProductDetailImage.objects.filter(product=product)
        for img in images:
            if img.image:
                img.image.delete(save=False)
            img.delete()
    
    @staticmethod
    def product_exists_by_name(name: str) -> bool:
        """
        بررسی وجود محصول بر اساس نام
        
        Args:
            name: نام محصول
        
        Returns:
            bool
        """
        return Product.objects.filter(name=name).exists()
    
    @staticmethod
    def product_exists_by_slug(slug: str) -> bool:
        """
        بررسی وجود محصول بر اساس slug
        
        Args:
            slug: slug محصول
        
        Returns:
            bool
        """
        return Product.objects.filter(slug=slug).exists()

    @staticmethod
    def get_product_count() -> int:
        """
        گرفتن تعداد کل محصولات
        
        Returns:
            int
        """
        return Product.objects.count()
    
    @staticmethod
    def get_available_product_count() -> int:
        """
        گرفتن تعداد محصولات موجود
        
        Returns:
            int
        """
        return Product.objects.filter(available=True).count()
    
    @staticmethod
    def get_product_with_images(product_id: int) -> Optional[Product]:
        """
        گرفتن محصول همراه با تصاویر مرتبط (بهینه‌شده با prefetch)
        
        Args:
            product_id: شناسهٔ محصول
        
        Returns:
            Product یا None
        """
        try:
            return Product.objects.prefetch_related('productdetailimage_set').get(id=product_id)
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def add_product_images(product: Product, images: List) -> int:
        """
        اضافه کردن تصاویر به محصول
        
        Args:
            product: شیء Product
            images: لیست فایل‌های عکس
        
        Returns:
            int: تعداد تصاویر اضافه‌شده
        """
        count = 0
        for img in images:
            ProductDetailImage.objects.create(product=product, image=img)
            count += 1
        return count
