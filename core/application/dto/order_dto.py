"""
Application Layer: Order DTOs
انتقال داده‌های سفارش‌ها
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class OrderItemDTO:
    """
    DTO برای آیتم سفارش
    """
    product_id: int
    product_name: str
    quantity: int
    price: float
    subtotal: float
    
    @classmethod
    def from_model(cls, order_item) -> 'OrderItemDTO':
        """
        ایجاد DTO از مدل OrderItem
        
        Args:
            order_item: شیء OrderItem
        
        Returns:
            OrderItemDTO: DTO آیتم سفارش
        """
        return cls(
            product_id=order_item.product.id,
            product_name=order_item.product.name,
            quantity=order_item.quantity,
            price=float(order_item.price),
            subtotal=float(order_item.subtotal)
        )


@dataclass
class OrderDTO:
    """
    DTO برای نمایش سفارش
    """
    id: int
    order_code: str
    status: str
    total_price: float
    created_at: datetime
    completed_at: Optional[datetime]
    items: List[OrderItemDTO] = field(default_factory=list)
    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @classmethod
    def from_model(cls, order) -> 'OrderDTO':
        """
        ایجاد DTO از مدل Order
        
        Args:
            order: شیء Order
        
        Returns:
            OrderDTO: DTO سفارش
        """
        items = [OrderItemDTO.from_model(item) for item in order.items.all()]
        
        return cls(
            id=order.id,
            order_code=order.order_code,
            status=order.status,
            total_price=float(order.total_price),
            created_at=order.created_at,
            completed_at=order.completed_at,
            items=items,
            user_id=order.user.id,
            username=order.user.username,
            first_name=order.user.first_name,
            last_name=order.user.last_name
        )


@dataclass
class OrderSummaryDTO:
    """
    DTO برای خلاصه سفارش
    """
    id: int
    order_code: str
    status: str
    total_price: float
    created_at: datetime
    items_count: int
    
    @classmethod
    def from_model(cls, order) -> 'OrderSummaryDTO':
        """
        ایجاد DTO از مدل Order
        
        Args:
            order: شیء Order
        
        Returns:
            OrderSummaryDTO: DTO خلاصه سفارش
        """
        return cls(
            id=order.id,
            order_code=order.order_code,
            status=order.status,
            total_price=float(order.total_price),
            created_at=order.created_at,
            items_count=order.items.count()
        )


@dataclass
class OrderManagementDTO:
    """
    DTO برای مدیریت سفارشات
    """
    id: int
    order_code: str
    status: str
    total_price: float
    created_at: datetime
    completed_at: Optional[datetime]
    user: Dict[str, Any]
    items_count: int
    
    @classmethod
    def from_model(cls, order) -> 'OrderManagementDTO':
        """
        ایجاد DTO از مدل Order برای مدیریت
        
        Args:
            order: شیء Order
        
        Returns:
            OrderManagementDTO: DTO مدیریت سفارش
        """
        return cls(
            id=order.id,
            order_code=order.order_code,
            status=order.status,
            total_price=float(order.total_price),
            created_at=order.created_at,
            completed_at=order.completed_at,
            user={
                'id': order.user.id,
                'username': order.user.username,
                'first_name': order.user.first_name,
                'last_name': order.user.last_name
            },
            items_count=order.items.count()
        )


@dataclass
class OrderStatisticsDTO:
    """
    DTO برای آمار سفارشات
    """
    total_orders: int
    pending_orders: int
    processing_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: float
    
    @classmethod
    def from_stats(cls, stats: Dict[str, Any]) -> 'OrderStatisticsDTO':
        """
        ایجاد DTO از آمار
        
        Args:
            stats: آمار سفارشات
        
        Returns:
            OrderStatisticsDTO: DTO آمار
        """
        return cls(
            total_orders=stats.get('total_orders', 0),
            pending_orders=stats.get('pending_orders', 0),
            processing_orders=stats.get('processing_orders', 0),
            delivered_orders=stats.get('delivered_orders', 0),
            cancelled_orders=stats.get('cancelled_orders', 0),
            total_revenue=stats.get('total_revenue', 0.0)
        )


@dataclass
class OrderResponseDTO:
    """
    DTO برای پاسخ عملیات سفارشات
    """
    success: bool
    message: str
    order_id: Optional[int] = None
    order_code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_response(cls, message: str, order_id: Optional[int] = None, order_code: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> 'OrderResponseDTO':
        """
        پاسخ موفق
        
        Args:
            message: پیام
            order_id: شناسه سفارش
            order_code: کد سفارش
            data: داده‌های اضافی
        
        Returns:
            OrderResponseDTO: DTO پاسخ
        """
        return cls(
            success=True,
            message=message,
            order_id=order_id,
            order_code=order_code,
            data=data
        )
    
    @classmethod
    def error_response(cls, message: str) -> 'OrderResponseDTO':
        """
        پاسخ خطا
        
        Args:
            message: پیام خطا
        
        Returns:
            OrderResponseDTO: DTO پاسخ
        """
        return cls(
            success=False,
            message=message
        )