"""
Application Layer: Cart Service

"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.http import HttpRequest

from ...domain.entities.cart_entity import CartEntity, CartItemEntity
from ...domain.validators.cart_validators import (
    validate_cart_quantity,
    validate_product_availability,
    validate_cart_item_data,
    validate_session_cart_data
)
from ...infrastructure.repositories.cart_repository import CartRepository
from ...infrastructure.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class CartException(Exception):
    """Exception اختصاصی برای خطاهای سبد خرید"""
    pass


class CartValidationException(CartException):
    """Exception برای خطاهای اعتبارسنجی سبد"""
    pass


class CartService:
    """
    سرویس مدیریت سبد خرید
    شامل اضافه کردن، حذف، بروزرسانی و نمایش سبد
    """

    MAX_QUANTITY_PER_ITEM = 5

    @classmethod
    def add_to_cart(
        cls,
        request: HttpRequest,
        product_slug: str,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        اضافه کردن محصول به سبد

        Args:
            request: HttpRequest
            product_slug: slug محصول
            quantity: تعداد

        Returns:
            Dict: نتیجه عملیات

        Raises:
            CartValidationException: خطاهای اعتبارسنجی
            CartException: خطاهای دیگر
        """
        try:
            # گرفتن محصول
            product = ProductRepository.get_product_by_slug(product_slug)
            if not product:
                raise CartException(f"محصول با slug {product_slug} پیدا نشد")

            # بررسی موجود بودن محصول
            validate_product_availability(product.available)

            # اعتبارسنجی تعداد
            quantity = min(quantity, cls.MAX_QUANTITY_PER_ITEM)
            validate_cart_quantity(quantity, cls.MAX_QUANTITY_PER_ITEM)

            user = request.user if request.user.is_authenticated else None

            if user:
                # کاربر لاگین کرده - کار با DB
                result = cls._add_to_authenticated_user_cart(user, product, quantity, request)
            else:
                # کاربر مهمان - کار با session
                result = cls._add_to_guest_user_cart(request, product, quantity)

            logger.info(f"محصول {product.name} به سبد {'کاربر' if user else 'مهمان'} اضافه شد")
            return result

        except Exception as e:
            logger.exception(f"خطا در اضافه کردن به سبد: {str(e)}")
            raise CartException(f"خطا در اضافه کردن به سبد: {str(e)}")

    @classmethod
    def _add_to_authenticated_user_cart(
        cls,
        user: User,
        product: Any,
        quantity: int,
        request: HttpRequest
    ) -> Dict[str, Any]:
        """
        اضافه کردن به سبد کاربر لاگین کرده

        Args:
            user: شیء User
            product: شیء Product
            quantity: تعداد
            request: HttpRequest

        Returns:
            Dict: نتیجه
        """
        # انتقال سبد session به DB اگر وجود داشته باشد
        session_cart = CartRepository.get_session_cart(request)
        if session_cart:
            CartRepository.migrate_session_cart_to_db(user, session_cart)
            CartRepository.clear_session_cart(request)

        # اضافه کردن محصول جدید
        cart_item = CartRepository.add_or_update_cart_item(user, product, quantity)

        return {
            'success': True,
            'quantity': cart_item.quantity,
            'message': f'محصول {product.name} به سبد اضافه شد'
        }

    @classmethod
    def _add_to_guest_user_cart(
        cls,
        request: HttpRequest,
        product: Any,
        quantity: int
    ) -> Dict[str, Any]:
        """
        اضافه کردن به سبد کاربر مهمان

        Args:
            request: HttpRequest
            product: شیء Product
            quantity: تعداد

        Returns:
            Dict: نتیجه
        """
        cart = CartRepository.get_session_cart(request)

        slug_str = str(product.slug)
        if slug_str in cart:
            new_quantity = min(cart[slug_str]['quantity'] + quantity, cls.MAX_QUANTITY_PER_ITEM)
            cart[slug_str]['quantity'] = new_quantity
        else:
            cart[slug_str] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
            }

        CartRepository.save_session_cart(request, cart)

        return {
            'success': True,
            'quantity': cart[slug_str]['quantity'],
            'message': f'محصول {product.name} به سبد اضافه شد'
        }

    @classmethod
    def get_cart_summary(cls, request: HttpRequest) -> Dict[str, Any]:
        """
        گرفتن خلاصه سبد خرید

        Args:
            request: HttpRequest

        Returns:
            Dict: خلاصه سبد
        """
        user = request.user if request.user.is_authenticated else None

        if user:
            cart_items_db = CartRepository.get_user_cart(user)
            cart_items = []
            total = Decimal('0.0')
            original_total = Decimal('0.0')

            for item in cart_items_db:
                product = item.product
                original_price = product.original_price or product.price
                price = product.price
                is_unavailable = not bool(product.available)

                total_price = price * item.quantity
                if not is_unavailable:
                    total += total_price
                    original_total += original_price * item.quantity

                cart_items.append({
                    'product': product,
                    'quantity': item.quantity,
                    'price': price,
                    'original_price': original_price,
                    'total_price': total_price,
                    'id': item.id,
                    'is_unavailable': is_unavailable
                })
        else:
            # سبد از session
            session_cart = CartRepository.get_session_cart(request)
            cart_items = []
            total = Decimal('0.0')
            original_total = Decimal('0.0')

            for slug, item in session_cart.items():
                product = ProductRepository.get_product_by_slug(slug)
                if not product:
                    continue

                quantity = item['quantity']
                price = Decimal(str(item['price']))
                original_price = product.original_price or price
                is_unavailable = not bool(product.available)

                total_price = price * quantity
                if not is_unavailable:
                    total += total_price
                    original_total += original_price * quantity

                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': price,
                    'original_price': original_price,
                    'total_price': total_price,
                    'id': slug,
                    'is_unavailable': is_unavailable
                })

        # محاسبه صرفه‌جویی
        savings = original_total - total
        if savings < 0:
            savings = Decimal('0.0')

        return {
            'cart_items': cart_items,
            'total': total,
            'original_total': original_total,
            'savings': savings,
            'total_items': sum(item['quantity'] for item in cart_items if not item.get('is_unavailable'))
        }

    @classmethod
    def remove_from_cart(cls, request: HttpRequest, item_id: int) -> Dict[str, Any]:
        """
        حذف آیتم از سبد (برای کاربران لاگین کرده)

        Args:
            request: HttpRequest
            item_id: شناسه آیتم سبد

        Returns:
            Dict: نتیجه

        Raises:
            CartException: اگر آیتم پیدا نشود
        """
        if not request.user.is_authenticated:
            raise CartException("این عملیات فقط برای کاربران لاگین کرده معتبر است")

        try:
            from core.infrastructure.models import Cart as CartModel
            cart_item = get_object_or_404(CartModel, id=item_id, user=request.user)
            product_name = cart_item.product.name
            CartRepository.remove_cart_item(cart_item)

            logger.info(f"آیتم {product_name} از سبد کاربر {request.user.username} حذف شد")

            return {
                'success': True,
                'message': f'🗑️ {product_name} از سبد حذف شد'
            }

        except Exception as e:
            logger.exception(f"خطا در حذف از سبد: {str(e)}")
            raise CartException(f"خطا در حذف از سبد: {str(e)}")

    @classmethod
    def set_cart_quantity(
        cls,
        request: HttpRequest,
        product_slug: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        تنظیم تعداد محصول در سبد

        Args:
            request: HttpRequest
            product_slug: slug محصول
            quantity: تعداد جدید (0 برای حذف)

        Returns:
            Dict: نتیجه عملیات

        Raises:
            CartValidationException: خطاهای اعتبارسنجی
        """
        try:
            # اعتبارسنجی تعداد
            quantity = max(0, min(int(quantity), cls.MAX_QUANTITY_PER_ITEM))

            user = request.user if request.user.is_authenticated else None

            if user:
                # کاربر لاگین کرده
                result = cls._set_authenticated_user_quantity(user, product_slug, quantity)
            else:
                # کاربر مهمان
                result = cls._set_guest_user_quantity(request, product_slug, quantity)

            # بروزرسانی خلاصه سبد
            summary = cls.get_cart_summary(request)
            result.update({
                'total': float(summary['total']),
                'original_total': float(summary['original_total']),
                'savings': float(summary['savings'])
            })

            return result

        except Exception as e:
            logger.exception(f"خطا در تنظیم تعداد: {str(e)}")
            raise CartException(f"خطا در تنظیم تعداد: {str(e)}")

    @classmethod
    def _set_authenticated_user_quantity(
        cls,
        user: User,
        product_slug: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        تنظیم تعداد برای کاربر لاگین کرده

        Args:
            user: شیء User
            product_slug: slug محصول
            quantity: تعداد

        Returns:
            Dict: نتیجه
        """
        product = ProductRepository.get_product_by_slug(product_slug)
        if not product:
            raise CartException(f"محصول با slug {product_slug} پیدا نشد")

        if quantity == 0:
            # حذف آیتم
            cart_item = CartRepository.get_cart_item(user, product)
            if cart_item:
                CartRepository.remove_cart_item(cart_item)
            message = "آیتم حذف شد"
        else:
            # بروزرسانی یا ایجاد آیتم
            cart_item = CartRepository.add_or_update_cart_item(user, product, quantity)
            message = "تعداد بروزرسانی شد" if cart_item.pk else "آیتم اضافه شد"

        return {
            'success': True,
            'quantity': quantity,
            'message': message
        }

    @classmethod
    def _set_guest_user_quantity(
        cls,
        request: HttpRequest,
        product_slug: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        تنظیم تعداد برای کاربر مهمان

        Args:
            request: HttpRequest
            product_slug: slug محصول
            quantity: تعداد

        Returns:
            Dict: نتیجه
        """
        cart = CartRepository.get_session_cart(request)

        if quantity == 0:
            # حذف آیتم
            if product_slug in cart:
                del cart[product_slug]
            message = "آیتم حذف شد"
        else:
            # بروزرسانی آیتم
            product = ProductRepository.get_product_by_slug(product_slug)
            if not product:
                raise CartException(f"محصول با slug {product_slug} پیدا نشد")

            cart[product_slug] = {
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity
            }
            message = "تعداد بروزرسانی شد"

        CartRepository.save_session_cart(request, cart)

        return {
            'success': True,
            'quantity': quantity,
            'message': message
        }

    @classmethod
    def clear_cart(cls, request: HttpRequest) -> Dict[str, Any]:
        """
        پاک کردن سبد خرید

        Args:
            request: HttpRequest

        Returns:
            Dict: نتیجه
        """
        user = request.user if request.user.is_authenticated else None

        if user:
            CartRepository.clear_user_cart(user)
        else:
            CartRepository.clear_session_cart(request)

        logger.info(f"سبد {'کاربر' if user else 'مهمان'} پاک شد")

        return {
            'success': True,
            'message': 'سبد خرید پاک شد'
        }