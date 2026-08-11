from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import uuid

class DelayedTask(models.Model):
    TASK_TYPE_CHOICES = [
        ('send_review_email', 'Send Review Request Email'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    scheduled_at = models.DateTimeField()
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.task_type} - {self.scheduled_at}"
