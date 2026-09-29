from django.urls import path, include
from core.interfaces.http.views.admin.order.admin_order_approval_view import *

urlpatterns = [

    path('order_reviews/', admin_order_reviews, name='admin_order_reviews'),
    path('order_reviews/<int:review_id>/accept/', admin_order_accept, name='admin_order_accept'),
    path('order_reviews/<int:review_id>/reject/', admin_order_reject, name='admin_order_reject'),
    path('order_reviews/<int:review_id>/delete/', admin_order_rejected_delete, name='admin_order_rejected_delete'),
    path('notifications/', admin_notifications, name='admin_notifications'),
    path('notifications/<int:notification_id>/open/', admin_notification_open, name='admin_notification_open'),

]