from django.urls import path
from django.urls import path, include
from .. import views
from core.interfaces.http.views.review_view import *

urlpatterns = [
    path('review_check/', review_check, name='review_check'),
    path('approve_review/<int:review_id>/', approve_review, name='approve_review'),
    path('delete_review/<int:review_id>/', delete_review, name='delete_review'),
    path('ban_user_from_review/<int:review_id>/', ban_user_from_review, name='ban_user_from_review'),
    path('add_review/<slug:slug>/', add_review, name='add_review'),
    # Blog reviews
    path('approve_blog_review/<int:review_id>/', approve_blog_review, name='approve_blog_review'),
    path('delete_blog_review/<int:review_id>/', delete_blog_review, name='delete_blog_review'),
    path('ban_user_from_blog_review/<int:review_id>/', ban_user_from_blog_review, name='ban_user_from_blog_review'),
]
