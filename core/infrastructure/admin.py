from django.contrib import admin
from .models import (
    GalleryImage,
    BlogPost,
    SlideshowMode,
    Slide,
    SlideButton,
    BadgeCategory,
    Badge,
    UserBadge,
    ClaimedBadgeReward,
    BadgeSettings,
)


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


class SlideButtonInline(admin.TabularInline):
    model = SlideButton
    extra = 0
    fields = ["text", "url", "sort_order"]


class SlideInline(admin.TabularInline):
    model = Slide
    extra = 0
    fields = ["image", "title", "text_position", "sort_order"]


@admin.register(SlideshowMode)
class SlideshowModeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "is_default", "expires_at", "created_at")
    list_filter = ("is_active", "is_default", "created_at")
    search_fields = ("name",)
    inlines = [SlideInline]


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ("id", "slideshow_mode", "sort_order", "text_position")
    list_filter = ("slideshow_mode", "text_position")
    inlines = [SlideButtonInline]


@admin.register(SlideButton)
class SlideButtonAdmin(admin.ModelAdmin):
    list_display = ("id", "slide", "text", "sort_order")
    list_filter = ("slide",)


@admin.register(BadgeCategory)
class BadgeCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_public", "sort_order", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("name",)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "level", "rarity", "is_public", "is_active", "sort_order")
    list_filter = ("category", "rarity", "is_public", "is_active")
    search_fields = ("name", "description")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "badge", "is_featured", "earned_at")
    list_filter = ("is_featured", "earned_at")
    search_fields = ("user__username", "badge__name")


@admin.register(ClaimedBadgeReward)
class ClaimedBadgeRewardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "badge", "order", "claimed_at")
    list_filter = ("claimed_at",)
    search_fields = ("user__username", "badge__name")


@admin.register(BadgeSettings)
class BadgeSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "enable_badges", "enable_rewards", "enable_congratulatory_emails", "badges_public", "badge_stats_public")
    list_filter = ("enable_badges", "enable_rewards", "enable_congratulatory_emails", "badges_public", "badge_stats_public")
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not BadgeSettings.objects.exists()
