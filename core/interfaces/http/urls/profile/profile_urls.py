from django.urls import path
from core.interfaces.http.views.profile.profile_view import *


urlpatterns = [
    path('profile/', profile, name='profile'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('user/<int:user_id>/', public_user_profile, name='public_user_profile'),
]
