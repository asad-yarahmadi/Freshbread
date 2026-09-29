from django.urls import path, include
from core.interfaces.http.views.admin.order.admin_order_management_view import *

urlpatterns = [

    path('manage_orders/', manage_orders, name='manage_orders'),
    path('deliver_verify/<int:order_id>/', deliver_verify, name='deliver_verify'),
    path('delivered_list/', delivered_list, name='delivered_list'),
    path('update_order_status/<int:order_id>/<str:new_status>/', update_order_status, name='update_order_status'),
    path('order_info/<int:order_id>/', order_info, name='order_info'),
]