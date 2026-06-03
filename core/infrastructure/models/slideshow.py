from django.db import models
from django.utils import timezone


class SlideshowMode(models.Model):
    TEXT_POSITION_CHOICES = [
        ('center', 'Center'),
        ('left', 'Left'),
        ('right', 'Right'),
    ]

    name = models.CharField(max_length=255, verbose_name="Mode Name")
    is_default = models.BooleanField(default=False, verbose_name="Is Default Mode")
    is_active = models.BooleanField(default=False, verbose_name="Is Currently Active")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expiry Date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-is_default', '-created_at']

    def __str__(self):
        return self.name

    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False


class Slide(models.Model):
    TEXT_POSITION_CHOICES = [
        ('center', 'Center'),
        ('left', 'Left'),
        ('right', 'Right'),
    ]

    slideshow_mode = models.ForeignKey(SlideshowMode, on_delete=models.CASCADE, related_name='slides')
    image = models.ImageField(upload_to='slides/', verbose_name="Slide Image (1920x1280 recommended)")
    title = models.CharField(max_length=255, blank=True, verbose_name="Slide Title")
    description = models.TextField(blank=True, verbose_name="Slide Description")
    text_position = models.CharField(max_length=20, choices=TEXT_POSITION_CHOICES, default='center', verbose_name="Text Position")
    sort_order = models.IntegerField(default=0, verbose_name="Sort Order")

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"Slide {self.id} - {self.title or 'Untitled'}"


class SlideButton(models.Model):
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE, related_name='buttons')
    text = models.CharField(max_length=255, verbose_name="Button Text")
    url = models.CharField(max_length=500, verbose_name="Button URL")
    sort_order = models.IntegerField(default=0, verbose_name="Sort Order")

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.text} - {self.slide}"
