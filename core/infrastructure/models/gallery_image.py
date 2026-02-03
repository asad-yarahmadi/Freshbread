from django.db import models


class GalleryImage(models.Model):
    image = models.ImageField(upload_to="gallery/%Y/%m/")
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"GalleryImage #{self.pk}"