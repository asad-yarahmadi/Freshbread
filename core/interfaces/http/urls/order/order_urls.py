from django.urls import path
from core.interfaces.http.views.order.order_view import *


urlpatterns = [
    path('order/<str:order_code>/', order_detail, name='order_detail'),
    path('cancel_order/<int:order_id>/', cancel_order, name='cancel_order'), 
    ]
