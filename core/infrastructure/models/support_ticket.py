from django.db import models
from django.contrib.auth.models import User


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("open", "Waiting for answer"),
        ("answered", "Answered"),
        ("closed", "Closed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="closed_tickets")

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"


class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = "Admin" if self.is_admin else (self.sender.username if self.sender else "User")
        return f"{who} @ {self.created_at:%Y-%m-%d %H:%M}"