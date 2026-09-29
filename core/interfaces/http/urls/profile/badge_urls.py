from django.urls import path, include
from core.interfaces.http.views.profile.badge_view import *

urlpatterns = [
        path('badges/', badge_explorer, name='badge_explorer'),
]