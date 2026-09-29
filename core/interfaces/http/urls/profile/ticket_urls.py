from django.urls import path
from core.interfaces.http.views.profile.ticket_view import tickets, ticket_new, ticket_detail

urlpatterns = [
    path('', tickets, name='tickets'),
    path('new/', ticket_new, name='ticket_new'),
    path('<int:ticket_id>/', ticket_detail, name='ticket_detail'),


]