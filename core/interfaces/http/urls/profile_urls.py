from django.urls import path
from django.urls import path, include
from .. import views
from core.interfaces.http.views.profile_view import *


urlpatterns = [
    path('profile/', profile, name='profile'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('user/<int:user_id>/', public_user_profile, name='public_user_profile'),
]
