from django.urls import path, include
from .. import views
from core.interfaces.http.views.product_view import *

urlpatterns=[
    path('manage/', manage_products, name='manage'),
    path('add/', add_product, name='add_product'),
    path('<slug:slug>/edit/', edit_product, name='edit_product'),
    path('<slug:slug>/delete/', delete_product, name='delete_product'),

]