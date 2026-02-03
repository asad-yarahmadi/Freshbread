"""
Infrastructure Layer: Order Repository
دسترسی به داده‌های سفارش‌ها
"""
import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from ...domain.entities.order_entity import OrderEntity, OrderItemEntity
from core.infrastructure.models import Order, OrderItem, Product

logger = logging.getLogger(__name__)


class OrderRepository:
    """
    Repository برای مدیریت سفارش‌ها
    """

    @classmethod
    def create_order(cls, order_data: Dict[str, Any]) -> Order:
        """
        ایجاد سفارش جدید
        
        Args:
            order_data: داده‌های سفارش
        
        Returns:
            Order: شیء سفارش ایجاد شده
        
        Raises:
            ValueError: اگر داده‌ها نامعتبر باشند
        """
        try:
            with transaction.atomic():
                # ایجاد سفارش
                order = Order.objects.create(
                    user_id=order_data['user_id'],
                    status=order_data.get('status', 'pending')
                )
                
                # افزودن آیتم‌ها
                for item_data in order_data['items']:
                    product = Product.objects.get(id=item_data['product_id'])
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                
                # بروزرسانی مجموع قیمت
                order.total_price = order.calculate_total()
                order.save(update_fields=['total_price'])
                
                logger.info(f"سفارش جدید ایجاد شد: {order.order_code}")
                return order
                
        except Exception as e:
            logger.exception(f"خطا در ایجاد سفارش: {str(e)}")
            raise ValueError(f"خطا در ایجاد سفارش: {str(e)}")

    @classmethod
    def get_order_by_id(cls, order_id: int) -> Optional[Order]:
        """
        گرفتن سفارش بر اساس شناسه
        
        Args:
            order_id: شناسه سفارش
        
        Returns:
            Order or None: شیء سفارش یا None
        """
        try:
            return Order.objects.select_related('user').prefetch_related('items__product').get(id=order_id)
        except Order.DoesNotExist:
            return None

    @classmethod
    def get_order_by_code(cls, order_code: str) -> Optional[Order]:
        """
        گرفتن سفارش بر اساس کد سفارش
        
        Args:
            order_code: کد سفارش
        
        Returns:
            Order or None: شیء سفارش یا None
        """
        try:
            return Order.objects.select_related('user').prefetch_related('items__product').get(order_code=order_code)
        except Order.DoesNotExist:
            return None

    @classmethod
    def get_user_orders(cls, user_id: int) -> List[Order]:
        """
        گرفتن سفارش‌های کاربر
        
        Args:
            user_id: شناسه کاربر
        
        Returns:
            List[Order]: لیست سفارش‌ها
        """
        return Order.objects.filter(user_id=user_id).select_related('user').prefetch_related('items__product').order_by('-created_at')

    @classmethod
    def get_all_orders(cls) -> List[Order]:
        """
        گرفتن تمام سفارش‌ها
        
        Returns:
            List[Order]: لیست سفارش‌ها
        """
        return Order.objects.all().select_related('user').prefetch_related('items__product').order_by('-created_at')

    @classmethod
    def update_order_status(cls, order_id: int, new_status: str) -> bool:
        """
        بروزرسانی وضعیت سفارش
        
        Args:
            order_id: شناسه سفارش
            new_status: وضعیت جدید
        
        Returns:
            bool: آیا بروزرسانی موفق بود
        """
        try:
            order = cls.get_order_by_id(order_id)
            if not order:
                return False
            
            order.status = new_status
            if new_status == 'delivered' and not order.completed_at:
                order.completed_at = timezone.now()
            
            order.save(update_fields=['status', 'completed_at'])

            if new_status == 'delivered':
                try:
                    from core.infrastructure.models import ReferralRecord, DiscountCode, Profile
                    rr_qs = ReferralRecord.objects.filter(used_by=order.user, has_order=False)
                    owner_ids = list(rr_qs.values_list('owner_id', flat=True))
                    rr_qs.update(has_order=True)
                    from django.utils import timezone
                    for oid in owner_ids:
                        count = ReferralRecord.objects.filter(owner_id=oid, has_order=True).count()
                        step = 7
                        target_awards = count // step
                        current_awards = DiscountCode.objects.filter(owner_id=oid, amount=50.00).count()
                        to_issue = max(0, target_awards - current_awards)
                        for _ in range(to_issue):
                            import secrets
                            code = secrets.token_hex(4).upper()
                            expires = timezone.now() + timezone.timedelta(days=14)
                            DiscountCode.objects.create(code=code, owner_id=oid, amount=50.00, expires_at=expires)
                            try:
                                from django.contrib.auth import get_user_model
                                from core.infrastructure.email.email_sender import email_sender
                                User = get_user_model()
                                owner = User.objects.get(id=oid)
                                if owner.email:
                                    email_sender.send(subject="Your $50 discount code", message=f"Code: {code}", to=owner.email, html_message=f"<p>Your discount code: <strong>{code}</strong></p>")
                            except Exception:
                                pass
                        Profile.objects.filter(user_id=oid).update(referral_used_count=count)
                except Exception:
                    pass

            logger.info(f"وضعیت سفارش {order.order_code} به {new_status} تغییر یافت")
            return True
            
        except Exception as e:
            logger.exception(f"خطا در بروزرسانی وضعیت سفارش: {str(e)}")
            return False

    @classmethod
    def cancel_order(cls, order_id: int) -> bool:
        """
        لغو سفارش
        
        Args:
            order_id: شناسه سفارش
        
        Returns:
            bool: آیا لغو موفق بود
        """
        try:
            order = cls.get_order_by_id(order_id)
            if not order:
                return False
            
            if order.status in ['delivered', 'cancelled']:
                return False
            
            order.status = 'cancelled'
            order.save(update_fields=['status'])
            
            logger.info(f"سفارش {order.order_code} لغو شد")
            return True
            
        except Exception as e:
            logger.exception(f"خطا در لغو سفارش: {str(e)}")
            return False

    @classmethod
    def get_orders_by_status(cls, status: str) -> List[Order]:
        """
        گرفتن سفارش‌ها بر اساس وضعیت
        
        Args:
            status: وضعیت سفارش
        
        Returns:
            List[Order]: لیست سفارش‌ها
        """
        return Order.objects.filter(status=status).select_related('user').prefetch_related('items__product').order_by('-created_at')

    @classmethod
    def get_recent_orders(cls, days: int = 7) -> List[Order]:
        """
        گرفتن سفارش‌های اخیر
        
        Args:
            days: تعداد روزها
        
        Returns:
            List[Order]: لیست سفارش‌ها
        """
        since = timezone.now() - timezone.timedelta(days=days)
        return Order.objects.filter(created_at__gte=since).select_related('user').prefetch_related('items__product').order_by('-created_at')

    @classmethod
    def get_order_statistics(cls) -> Dict[str, Any]:
        """
        گرفتن آمار سفارش‌ها
        
        Returns:
            Dict: آمار سفارش‌ها
        """
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        
        total_revenue = Order.objects.filter(status='delivered').aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')
        
        return {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
            'total_revenue': float(total_revenue)
        }

    @classmethod
    def delete_order(cls, order_id: int) -> bool:
        """
        حذف سفارش
        
        Args:
            order_id: شناسه سفارش
        
        Returns:
            bool: آیا حذف موفق بود
        """
        try:
            order = cls.get_order_by_id(order_id)
            if not order:
                return False
            
            order_code = order.order_code
            order.delete()
            
            logger.info(f"سفارش {order_code} حذف شد")
            return True
            
        except Exception as e:
            logger.exception(f"خطا در حذف سفارش: {str(e)}")
            return False