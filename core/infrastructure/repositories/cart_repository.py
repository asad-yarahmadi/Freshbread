"""
Infrastructure Layer: Cart Repository
دسترسی به مدل Cart و مدیریت session
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import User

from core.infrastructure.models import Cart as CartModel, Product


class CartRepository:
    """
    Repository برای مدیریت دسترسی به سبد خرید
    """

    @staticmethod
    def get_user_cart(user: User) -> List[CartModel]:
        """
        گرفتن سبد خرید کاربر از DB

        Args:
            user: شیء User

        Returns:
            List[CartModel]: لیست آیتم‌های سبد
        """
        return list(
            CartModel.objects.filter(user=user)
            .select_related('product')
            .order_by('-added_at')
        )

    @staticmethod
    def get_cart_item(user: User, product: Product) -> Optional[CartModel]:
        """
        گرفتن آیتم خاص از سبد

        Args:
            user: شیء User
            product: شیء Product

        Returns:
            CartModel یا None
        """
        try:
            return CartModel.objects.get(user=user, product=product)
        except CartModel.DoesNotExist:
            return None

    @staticmethod
    def add_or_update_cart_item(user: User, product: Product, quantity: int) -> CartModel:
        """
        اضافه کردن یا بروزرسانی آیتم در سبد

        Args:
            user: شیء User
            product: شیء Product
            quantity: تعداد

        Returns:
            CartModel: آیتم سبد بروزرسانی شده
        """
        cart_item, created = CartModel.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity'])

        return cart_item

    @staticmethod
    def update_cart_item_quantity(cart_item: CartModel, quantity: int) -> CartModel:
        """
        بروزرسانی تعداد آیتم سبد

        Args:
            cart_item: شیء CartModel
            quantity: تعداد جدید

        Returns:
            CartModel: آیتم بروزرسانی شده
        """
        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity'])
        return cart_item

    @staticmethod
    def remove_cart_item(cart_item: CartModel) -> None:
        """
        حذف آیتم از سبد

        Args:
            cart_item: شیء CartModel
        """
        cart_item.delete()

    @staticmethod
    def clear_user_cart(user: User) -> None:
        """
        پاک کردن تمام سبد کاربر

        Args:
            user: شیء User
        """
        CartModel.objects.filter(user=user).delete()

    @staticmethod
    def get_cart_total_items(user: User) -> int:
        """
        گرفتن تعداد کل آیتم‌های سبد کاربر

        Args:
            user: شیء User

        Returns:
            int: تعداد کل آیتم‌ها
        """
        from django.db.models import Sum
        result = CartModel.objects.filter(user=user).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        return result

    @staticmethod
    def get_cart_total_price(user: User) -> Decimal:
        """
        گرفتن قیمت کل سبد کاربر

        Args:
            user: شیء User

        Returns:
            Decimal: قیمت کل
        """
        from django.db.models import F, Sum
        result = CartModel.objects.filter(user=user).aggregate(
            total=Sum(F('quantity') * F('product__price'))
        )['total']
        return result or Decimal('0.0')

    @staticmethod
    def migrate_session_cart_to_db(user: User, session_cart: Dict[str, Any]) -> None:
        """
        انتقال سبد session به DB

        Args:
            user: شیء User
            session_cart: سبد session
        """
        for slug, item_data in session_cart.items():
            try:
                product = Product.objects.get(slug=slug, available=True)
                quantity = min(int(item_data['quantity']), 5)  # محدودیت 5

                cart_item, _ = CartModel.objects.get_or_create(
                    user=user,
                    product=product,
                    defaults={'quantity': quantity}
                )

                if cart_item.quantity + quantity <= 5:
                    cart_item.quantity += quantity
                else:
                    cart_item.quantity = 5

                cart_item.save()

            except Product.DoesNotExist:
                continue  # محصول پیدا نشد، رد می‌کنیم

    @staticmethod
    def get_session_cart(request) -> Dict[str, Any]:
        """
        گرفتن سبد از session

        Args:
            request: HttpRequest

        Returns:
            Dict: سبد session
        """
        return request.session.get('cart', {})

    @staticmethod
    def save_session_cart(request, cart_data: Dict[str, Any]) -> None:
        """
        ذخیره سبد در session

        Args:
            request: HttpRequest
            cart_data: داده‌های سبد
        """
        request.session['cart'] = cart_data
        request.session.modified = True

    @staticmethod
    def clear_session_cart(request) -> None:
        """
        پاک کردن سبد از session

        Args:
            request: HttpRequest
        """
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

    @staticmethod
    def cart_item_exists(user: User, product: Product) -> bool:
        """
        بررسی وجود آیتم در سبد

        Args:
            user: شیء User
            product: شیء Product

        Returns:
            bool
        """
        return CartModel.objects.filter(user=user, product=product).exists()