from django.urls import path, include
from .. import views
from core.interfaces.http.views.cart_view import *

urlpatterns=[
    path('', reservation, name='reservation'),
    path('add_to_cart/<slug:slug>/<int:quantity>/', add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('set_cart_quantity/<slug:slug>/<int:quantity>/', set_cart_quantity, name='set_cart_quantity'),
]