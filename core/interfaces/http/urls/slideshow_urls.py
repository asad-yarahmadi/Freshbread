from django.urls import path
from core.interfaces.http.views.slideshow_view import *

urlpatterns = [
    path('manage/', manage_slideshow, name='manage_slideshow'),
    path('add-mode/', add_slideshow_mode, name='add_slideshow_mode'),
    path('mode/<int:mode_id>/edit/', edit_slideshow_mode, name='edit_slideshow_mode'),
    path('mode/<int:mode_id>/delete/', delete_slideshow_mode, name='delete_slideshow_mode'),
    path('mode/<int:mode_id>/set-active/', set_active_slideshow, name='set_active_slideshow'),
    path('mode/<int:mode_id>/add-slide/', add_slide, name='add_slide'),
    path('slide/<int:slide_id>/edit/', edit_slide, name='edit_slide'),
    path('slide/<int:slide_id>/delete/', delete_slide, name='delete_slide'),
    path('slide/<int:slide_id>/add-button/', add_slide_button, name='add_slide_button'),
    path('button/<int:button_id>/edit/', edit_slide_button, name='edit_slide_button'),
    path('button/<int:button_id>/delete/', delete_slide_button, name='delete_slide_button'),
]
