from django.urls import path, include
from core.interfaces.http.views.blog_view import *

urlpatterns = [
    path('', blog, name='blog'),
    path('add/', blog_add, name='blog_add'),
    path('manage/', blog_manage, name='blog_manage'),
    path('<slug:slug>/review/add/', blog_add_review, name='blog_add_review'),
    path('<slug:slug>/like/', blog_like, name='blog_like'),
    path('<slug:slug>/edit/', blog_edit, name='blog_edit'),
    path('<slug:slug>/delete/', blog_delete, name='blog_delete'),
    path('<slug:slug>/', blog_details, name='blog_details'),
]