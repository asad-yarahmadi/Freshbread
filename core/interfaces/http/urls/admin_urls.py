from django.urls import path
from core.interfaces.http.views.admin_email_view import admin_email
from core.interfaces.http.views.admin_user_view import admin_users, admin_user_detail

urlpatterns = [
    path('email/', admin_email, name='admin_email'),
    path('users/', admin_users, name='admin_users'),
    path('users/<int:user_id>/', admin_user_detail, name='admin_user_detail'),
]