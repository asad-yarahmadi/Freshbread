from django.urls import path, include
from core.interfaces.http.views.profile.location_view import *

urlpatterns= [
    path('', locations_manage_view, name='locations_manage'),
    path('add/', location_add_view, name='location_add'),
    path('<int:pk>/edit/', location_edit_view, name='location_edit'),
    path('<int:pk>/delete/', location_delete_view, name='location_delete'),

]