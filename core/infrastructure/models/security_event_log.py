from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SecurityEventLog(models.Model):
    EVENT_LOCK = "lock"
    EVENT_UNLOCK = "unlock"
    EVENT_DDOS = "ddos_trigger"

    EVENT_CHOICES = [
        (EVENT_LOCK, "Lock"),
        (EVENT_UNLOCK, "Unlock"),
        (EVENT_DDOS, "DDoS Trigger"),
    ]

    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
