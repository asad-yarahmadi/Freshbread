from django.db import models
from django.contrib.auth.models import User

class ScheduledEmail(models.Model):
    AUDIENCE_CHOICES = [
        ("all", "All Users"),
        ("admins", "Admins Only"),
        ("users", "Users Only"),
    ]
    REPEAT_CHOICES = [
        ("none", "Send Once"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("custom", "Custom Interval"),
    ]

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    body_template = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="all")
    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default="none")
    interval_days = models.PositiveIntegerField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} ({self.audience}, {self.repeat})"