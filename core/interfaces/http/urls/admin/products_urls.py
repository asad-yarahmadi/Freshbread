from django.urls import path, include
from core.interfaces.http.views.admin.admin_product_view import *

urlpatterns=[
    path('manage/', manage_products, name='manage'),
    path('add/', add_product, name='add_product'),
    path('<slug:slug>/edit/', edit_product, name='edit_product'),
    path('<slug:slug>/delete/', delete_product, name='delete_product'),
    path('update-category-order/', update_category_order, name='update_category_order'),
    path('update-product-order/', update_product_order, name='update_product_order'),
]