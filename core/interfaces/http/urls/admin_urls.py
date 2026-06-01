from django.urls import path
from core.interfaces.http.views.admin_email_view import admin_email
from core.interfaces.http.views.admin_user_view import admin_users, admin_user_detail
from core.interfaces.http.views.admin_security_view import admin_security
from core.interfaces.http.views.admin_announcement_view import admin_announcements
from core.interfaces.http.views.admin_release_view import admin_releases
from core.interfaces.http.views.admin_block_url_view import manage_urls, log_list

urlpatterns = [
    path('email/', admin_email, name='admin_email'),
    path('users/', admin_users, name='admin_users'),
    path('users/<int:user_id>/', admin_user_detail, name='admin_user_detail'),
    path('security/', admin_security, name='admin_security'),
    path('announcements/', admin_announcements, name='admin_announcements'),
    path('releases/', admin_releases, name='admin_releases'),
    path('urls/', manage_urls, name='manage_urls'),
    path('logs/', log_list, name='log_list'),


]
