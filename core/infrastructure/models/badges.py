from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class BadgeCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Badge(models.Model):
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    
    PROGRESS_TYPE_CHOICES = [
        ('count', 'Count'),
        ('duration', 'Duration'),
    ]

    category = models.ForeignKey(BadgeCategory, on_delete=models.CASCADE, related_name='badges')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    requirement = models.TextField(blank=True, null=True)
    level = models.PositiveSmallIntegerField()
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    color = models.CharField(max_length=20, default='#000000')
    icon_svg = models.FileField(upload_to='badges/icons/svg/', blank=True, null=True)
    icon_webp = models.ImageField(upload_to='badges/icons/webp/', blank=True, null=True)
    progress_type = models.CharField(max_length=20, choices=PROGRESS_TYPE_CHOICES, default='count')
    progress_target = models.PositiveIntegerField(default=1)
    is_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Our custom fields for the badge system
    reward_text = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['category', 'sort_order', 'level']
        unique_together = ['category', 'level']

    def __str__(self):
        return f"{self.name} (Level {self.level} - {self.category})"


class UserBadge(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    congratulatory_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-earned_at']
        unique_together = ['user', 'badge']

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class ClaimedBadgeReward(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='claimed_rewards')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='claimed_rewards')
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='claimed_rewards', blank=True, null=True)
    claimed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-claimed_at']
        unique_together = ['user', 'badge']

    def __str__(self):
        return f"{self.user.username} - {self.badge.name} reward claimed"


class BadgeSettings(models.Model):
    SORT_METHOD_CHOICES = [
        ('level', 'By Level'),
        ('date_earned', 'By Date Earned'),
        ('rarity', 'By Rarity'),
        ('category', 'By Category'),
    ]
    
    enable_badges = models.BooleanField(default=True)
    enable_rewards = models.BooleanField(default=True)
    enable_congratulatory_emails = models.BooleanField(default=True)
    badges_public = models.BooleanField(default=True)
    badge_stats_public = models.BooleanField(default=True)
    max_visible_badges = models.PositiveIntegerField(default=10)
    sort_method = models.CharField(max_length=20, choices=SORT_METHOD_CHOICES, default='level')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Badge Settings"

    def __str__(self):
        return "Badge Settings"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if BadgeSettings.objects.exists() and not self.pk:
            raise ValueError("Only one BadgeSettings instance can exist")
        super().save(*args, **kwargs)
