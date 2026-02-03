"""
Domain Layer: Order Entity
Entity سفارش‌ها با validation داخلی
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field

from ...infrastructure.models import Order as OrderModel, OrderItem as OrderItemModel


@dataclass
class OrderItemEntity:
    """
    Entity آیتم سفارش
    """
    product_id: int
    product_name: str
    quantity: int
    price: Decimal
    subtotal: Decimal = field(init=False)

    def __post_init__(self):
        self.subtotal = self.quantity * self.price

    @classmethod
    def from_model(cls, order_item: OrderItemModel) -> 'OrderItemEntity':
        """
        ایجاد Entity از مدل OrderItem
        
        Args:
            order_item: شیء OrderItem
        
        Returns:
            OrderItemEntity: Entity آیتم سفارش
        """
        return cls(
            product_id=order_item.product.id,
            product_name=order_item.product.name,
            quantity=order_item.quantity,
            price=order_item.price
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل به dictionary
        
        Returns:
            Dict: داده‌های آیتم
        """
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': float(self.price),
            'subtotal': float(self.subtotal)
        }


@dataclass
class OrderEntity:
    """
    Entity سفارش
    """
    id: Optional[int]
    user_id: int
    order_code: str
    status: str
    items: List[OrderItemEntity] = field(default_factory=list)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_price: Decimal = field(init=False)

    VALID_STATUSES = ['pending', 'processing', 'cooking', 'queued', 'sending', 'ready', 'delivered', 'cancelled']
    VALID_TRANSITIONS = {
        'pending': ['processing', 'cancelled'],
        'processing': ['cooking', 'cancelled'],
        'cooking': ['queued', 'cancelled'],
        'queued': ['sending', 'ready', 'cancelled'],
        'sending': ['delivered', 'cancelled'],
        'ready': ['delivered', 'cancelled'],
        'delivered': [],
        'cancelled': []
    }

    def __post_init__(self):
        self._calculate_total()

    def _calculate_total(self) -> None:
        """محاسبه مجموع قیمت سفارش"""
        self.total_price = sum(item.subtotal for item in self.items)

    def add_item(self, item: OrderItemEntity) -> None:
        """
        افزودن آیتم به سفارش
        
        Args:
            item: آیتم سفارش
        """
        self.items.append(item)
        self._calculate_total()

    def remove_item(self, product_id: int) -> bool:
        """
        حذف آیتم از سفارش
        
        Args:
            product_id: شناسه محصول
        
        Returns:
            bool: آیا آیتم حذف شد
        """
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                del self.items[i]
                self._calculate_total()
                return True
        return False

    def update_item_quantity(self, product_id: int, quantity: int) -> bool:
        """
        بروزرسانی تعداد آیتم
        
        Args:
            product_id: شناسه محصول
            quantity: تعداد جدید
        
        Returns:
            bool: آیا بروزرسانی شد
        """
        for item in self.items:
            if item.product_id == product_id:
                item.quantity = quantity
                item.subtotal = item.quantity * item.price
                self._calculate_total()
                return True
        return False

    def can_transition_to(self, new_status: str) -> bool:
        """
        بررسی امکان تغییر وضعیت
        
        Args:
            new_status: وضعیت جدید
        
        Returns:
            bool: آیا تغییر ممکن است
        """
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def transition_to(self, new_status: str) -> bool:
        """
        تغییر وضعیت سفارش
        
        Args:
            new_status: وضعیت جدید
        
        Returns:
            bool: آیا تغییر انجام شد
        """
        if self.can_transition_to(new_status):
            self.status = new_status
            if new_status == 'delivered' and not self.completed_at:
                from datetime import datetime
                self.completed_at = datetime.now()
            return True
        return False

    @classmethod
    def from_model(cls, order: OrderModel) -> 'OrderEntity':
        """
        ایجاد Entity از مدل Order
        
        Args:
            order: شیء Order
        
        Returns:
            OrderEntity: Entity سفارش
        """
        items = [OrderItemEntity.from_model(item) for item in order.items.all()]
        
        return cls(
            id=order.id,
            user_id=order.user.id,
            order_code=order.order_code,
            status=order.status,
            items=items,
            created_at=order.created_at,
            completed_at=order.completed_at
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        تبدیل به dictionary
        
        Returns:
            Dict: داده‌های سفارش
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_code': self.order_code,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'total_price': float(self.total_price),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }