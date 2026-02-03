from django.urls import path
from core.interfaces.http.views.ticket_view import tickets, ticket_new, ticket_detail, admin_tickets, admin_ticket_detail

urlpatterns = [
    path('', tickets, name='tickets'),
    path('new/', ticket_new, name='ticket_new'),
    path('<int:ticket_id>/', ticket_detail, name='ticket_detail'),

    # Admin
    path('admin/', admin_tickets, name='admin_tickets'),
    path('admin/<int:ticket_id>/', admin_ticket_detail, name='admin_ticket_detail'),
]