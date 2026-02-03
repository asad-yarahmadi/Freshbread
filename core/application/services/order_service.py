"""
Application Layer: Order Service
منطق تجاری سفارش‌ها
"""
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction

from ...domain.entities.order_entity import OrderEntity, OrderItemEntity
from ...domain.validators.order_validators import (
    validate_order_data,
    validate_order_status,
    validate_order_transition,
    validate_order_cancellation
)
from ...infrastructure.repositories.order_repository import OrderRepository
from ...infrastructure.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class OrderException(Exception):
    """Exception اختصاصی برای خطاهای سفارش"""
    pass


class OrderValidationException(OrderException):
    """Exception برای خطاهای اعتبارسنجی سفارش"""
    pass


class OrderService:
    """
    سرویس مدیریت سفارش‌ها
    شامل ایجاد، بروزرسانی وضعیت، لغو و مدیریت سفارش‌ها
    """

    @classmethod
    def create_order(cls, user: User, cart_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ایجاد سفارش جدید از سبد خرید
        
        Args:
            user: کاربر
            cart_items: آیتم‌های سبد خرید
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            OrderValidationException: خطاهای اعتبارسنجی
            OrderException: خطاهای دیگر
        """
        try:
            # آماده‌سازی داده‌ها
            order_data = {
                'user_id': user.id,
                'items': []
            }
            
            for item in cart_items:
                product = ProductRepository.get_product_by_id(item['product_id'])
                if not product:
                    raise OrderException(f"محصول با شناسه {item['product_id']} پیدا نشد")
                
                if not product.available:
                    raise OrderException(f"محصول {product.name} موجود نیست")
                
                order_data['items'].append({
                    'product_id': product.id,
                    'quantity': item['quantity'],
                    'price': product.price
                })
            
            # اعتبارسنجی داده‌ها
            validate_order_data(order_data)
            
            # ایجاد سفارش
            order = OrderRepository.create_order(order_data)
            
            logger.info(f"سفارش جدید برای کاربر {user.username} ایجاد شد: {order.order_code}")
            
            return {
                'success': True,
                'order_id': order.id,
                'order_code': order.order_code,
                'total_price': float(order.total_price),
                'message': f'سفارش شما با کد {order.order_code} ثبت شد'
            }
            
        except Exception as e:
            logger.exception(f"خطا در ایجاد سفارش: {str(e)}")
            raise OrderException(f"خطا در ایجاد سفارش: {str(e)}")

    @classmethod
    def get_order_details(cls, order_code: str, user: Optional[User] = None) -> Dict[str, Any]:
        """
        گرفتن جزئیات سفارش
        
        Args:
            order_code: کد سفارش
            user: کاربر (برای بررسی دسترسی)
        
        Returns:
            Dict: جزئیات سفارش
        
        Raises:
            OrderException: اگر سفارش پیدا نشود یا دسترسی مجاز نباشد
        """
        try:
            order = OrderRepository.get_order_by_code(order_code)
            if not order:
                raise OrderException(f"سفارش با کد {order_code} پیدا نشد")
            
            # بررسی دسترسی
            if user and not user.is_staff and order.user != user:
                raise OrderException("شما اجازه مشاهده این سفارش را ندارید")
            
            order_entity = OrderEntity.from_model(order)
            
            return {
                'order': order_entity.to_dict(),
                'user': {
                    'id': order.user.id,
                    'username': order.user.username,
                    'first_name': order.user.first_name,
                    'last_name': order.user.last_name
                }
            }
            
        except Exception as e:
            logger.exception(f"خطا در گرفتن جزئیات سفارش: {str(e)}")
            raise OrderException(f"خطا در گرفتن جزئیات سفارش: {str(e)}")

    @classmethod
    def update_order_status(cls, order_id: int, new_status: str) -> Dict[str, Any]:
        """
        بروزرسانی وضعیت سفارش
        
        Args:
            order_id: شناسه سفارش
            new_status: وضعیت جدید
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            OrderValidationException: خطاهای اعتبارسنجی
            OrderException: خطاهای دیگر
        """
        try:
            # گرفتن سفارش فعلی
            order = OrderRepository.get_order_by_id(order_id)
            if not order:
                raise OrderException(f"سفارش با شناسه {order_id} پیدا نشد")
            
            # اعتبارسنجی تغییر وضعیت
            validate_order_transition(order.status, new_status)
            
            # بروزرسانی وضعیت
            success = OrderRepository.update_order_status(order_id, new_status)
            if not success:
                raise OrderException("خطا در بروزرسانی وضعیت سفارش")
            
            logger.info(f"وضعیت سفارش {order.order_code} به {new_status} تغییر یافت")

            if new_status == 'queued':
                try:
                    from django.core.mail import send_mail
                    if order.user.email:
                        send_mail(
                            subject='Your order is coming soon!',
                            message='Your order entered the sending line and will be on the way soon.',
                            from_email=None,
                            recipient_list=[order.user.email],
                            fail_silently=True,
                        )
                except Exception:
                    pass
            if new_status == 'ready' and not order.deliver:
                try:
                    from django.core.mail import send_mail
                    if order.user.email:
                        send_mail(
                            subject='Your order is ready for pickup',
                            message='Your order is ready for pickup. Please visit the counter with your order code.',
                            from_email=None,
                            recipient_list=[order.user.email],
                            fail_silently=True,
                        )
                except Exception:
                    pass
            
            return {
                'success': True,
                'order_code': order.order_code,
                'old_status': order.status,
                'new_status': new_status,
                'message': f'وضعیت سفارش {order.order_code} به {new_status} تغییر یافت'
            }
            
        except OrderValidationException:
            raise
        except Exception as e:
            logger.exception(f"خطا در بروزرسانی وضعیت سفارش: {str(e)}")
            raise OrderException(f"خطا در بروزرسانی وضعیت سفارش: {str(e)}")

    @classmethod
    def cancel_order(cls, order_id: int, user: Optional[User] = None) -> Dict[str, Any]:
        """
        لغو سفارش
        
        Args:
            order_id: شناسه سفارش
            user: کاربر (برای بررسی دسترسی)
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            OrderValidationException: خطاهای اعتبارسنجی
            OrderException: خطاهای دیگر
        """
        try:
            # گرفتن سفارش
            order = OrderRepository.get_order_by_id(order_id)
            if not order:
                raise OrderException(f"سفارش با شناسه {order_id} پیدا نشد")
            
            # بررسی دسترسی
            if user and not user.is_staff and order.user != user:
                raise OrderException("شما اجازه لغو این سفارش را ندارید")
            
            # اعتبارسنجی امکان لغو
            validate_order_cancellation(order.status)
            
            # لغو سفارش
            success = OrderRepository.cancel_order(order_id)
            if not success:
                raise OrderException("خطا در لغو سفارش")
            
            logger.info(f"سفارش {order.order_code} لغو شد")
            
            return {
                'success': True,
                'order_code': order.order_code,
                'message': f'سفارش {order.order_code} لغو شد'
            }
            
        except OrderValidationException:
            raise
        except Exception as e:
            logger.exception(f"خطا در لغو سفارش: {str(e)}")
            raise OrderException(f"خطا در لغو سفارش: {str(e)}")

    @classmethod
    def get_user_orders(cls, user: User) -> List[Dict[str, Any]]:
        """
        گرفتن سفارش‌های کاربر
        
        Args:
            user: کاربر
        
        Returns:
            List[Dict]: لیست سفارش‌ها
        """
        try:
            orders = OrderRepository.get_user_orders(user.id)
            return [
                {
                    'id': order.id,
                    'order_code': order.order_code,
                    'status': order.status,
                    'total_price': float(order.total_price),
                    'created_at': order.created_at.isoformat(),
                    'completed_at': order.completed_at.isoformat() if order.completed_at else None,
                    'items_count': order.items.count()
                }
                for order in orders
            ]
            
        except Exception as e:
            logger.exception(f"خطا در گرفتن سفارش‌های کاربر: {str(e)}")
            raise OrderException(f"خطا در گرفتن سفارش‌های کاربر: {str(e)}")

    @classmethod
    def get_all_orders(cls) -> List[Dict[str, Any]]:
        """
        گرفتن تمام سفارش‌ها برای مدیریت
        
        Returns:
            List[Dict]: لیست سفارش‌ها
        """
        try:
            orders = OrderRepository.get_all_orders()
            return [
                {
                    'id': order.id,
                    'order_code': order.order_code,
                    'user': {
                        'id': order.user.id,
                        'username': order.user.username,
                        'first_name': order.user.first_name,
                        'last_name': order.user.last_name
                    },
                    'status': order.status,
                    'total_price': float(order.total_price),
                    'created_at': order.created_at.isoformat(),
                    'completed_at': order.completed_at.isoformat() if order.completed_at else None,
                    'items_count': order.items.count()
                }
                for order in orders
            ]
            
        except Exception as e:
            logger.exception(f"خطا در گرفتن تمام سفارش‌ها: {str(e)}")
            raise OrderException(f"خطا در گرفتن تمام سفارش‌ها: {str(e)}")

    @classmethod
    def get_order_statistics(cls) -> Dict[str, Any]:
        """
        گرفتن آمار سفارش‌ها
        
        Returns:
            Dict: آمار سفارش‌ها
        """
        try:
            return OrderRepository.get_order_statistics()
        except Exception as e:
            logger.exception(f"خطا در گرفتن آمار سفارش‌ها: {str(e)}")
            raise OrderException(f"خطا در گرفتن آمار سفارش‌ها: {str(e)}")

    @classmethod
    def delete_order(cls, order_id: int) -> Dict[str, Any]:
        """
        حذف سفارش
        
        Args:
            order_id: شناسه سفارش
        
        Returns:
            Dict: نتیجه عملیات
        
        Raises:
            OrderException: اگر سفارش پیدا نشود
        """
        try:
            order = OrderRepository.get_order_by_id(order_id)
            if not order:
                raise OrderException(f"سفارش با شناسه {order_id} پیدا نشد")
            
            order_code = order.order_code
            success = OrderRepository.delete_order(order_id)
            
            if not success:
                raise OrderException("خطا در حذف سفارش")
            
            logger.info(f"سفارش {order_code} حذف شد")
            
            return {
                'success': True,
                'order_code': order_code,
                'message': f'سفارش {order_code} حذف شد'
            }
            
        except Exception as e:
            logger.exception(f"خطا در حذف سفارش: {str(e)}")
            raise OrderException(f"خطا در حذف سفارش: {str(e)}")