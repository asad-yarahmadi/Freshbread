from django.urls import path
from core.interfaces.http.views.order_view import *


urlpatterns = [
    path('order/<str:order_code>/', order_detail, name='order_detail'),
    path('manage_orders/', manage_orders, name='manage_orders'),
    path('deliver_verify/<int:order_id>/', deliver_verify, name='deliver_verify'),
    path('delivered_list/', delivered_list, name='delivered_list'),
    path('update_order_status/<int:order_id>/<str:new_status>/', update_order_status, name='update_order_status'),
    path('cancel_order/<int:order_id>/', cancel_order, name='cancel_order'),
    path('order_info/<int:order_id>/', order_info, name='order_info'),
    path('locations/', locations_manage_view, name='locations_manage'),
    path('locations/add/', location_add_view, name='location_add'),
    path('locations/<int:pk>/edit/', location_edit_view, name='location_edit'),
    path('locations/<int:pk>/delete/', location_delete_view, name='location_delete'),
    path('order_reviews/', admin_order_reviews, name='admin_order_reviews'),
    path('order_reviews/<int:review_id>/accept/', admin_order_accept, name='admin_order_accept'),
    path('order_reviews/<int:review_id>/reject/', admin_order_reject, name='admin_order_reject'),
    path('order_reviews/<int:review_id>/delete/', admin_order_rejected_delete, name='admin_order_rejected_delete'),
    path('notifications/', admin_notifications, name='admin_notifications'),
    path('notifications/<int:notification_id>/open/', admin_notification_open, name='admin_notification_open'),
]
