from django.db import models

class BlockedURL(models.Model):
    path = models.CharField(max_length=500, unique=True)
    reason = models.TextField()
    blocked_at = models.DateTimeField(auto_now_add=True)
    blocked_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.path


class BlockLog(models.Model):
    blocked_url = models.ForeignKey(BlockedURL, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)  # 'block' or 'unblock'
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.action} - {self.blocked_url.path}"