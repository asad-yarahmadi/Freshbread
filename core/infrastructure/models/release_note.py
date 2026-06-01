from django.db import models


class ReleaseNote(models.Model):
    version = models.CharField(max_length=32, unique=True)
    release_date = models.DateField()
    features = models.TextField(blank=True)
    bug_fixes = models.TextField(blank=True)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-release_date", "-created_at"]

    def __str__(self):
        return self.version
