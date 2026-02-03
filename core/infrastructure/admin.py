from django.contrib import admin
from .models import GalleryImage, BlogPost


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("title",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "is_published", "likes_count", "views_count", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "seo_keywords", "tags")