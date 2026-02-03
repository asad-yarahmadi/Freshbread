from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from core.infrastructure.models import SupportTicket, TicketMessage
from core.infrastructure.email.email_sender import email_sender
from core.interfaces.http.decorators import admin_login_protect


@login_required
def tickets(request):
    qs = SupportTicket.objects.filter(user=request.user).order_by('-updated_at')
    return render(request, 'freshbread/tickets/list.html', {"tickets": qs})


@login_required
def ticket_new(request):
    if request.method == 'POST':
        subject = (request.POST.get('subject') or '').strip()
        message = (request.POST.get('message') or '').strip()
        if not subject or not message:
            messages.error(request, 'Please fill subject and message.')
            return redirect('ticket_new')
        t = SupportTicket.objects.create(user=request.user, subject=subject, status='open')
        TicketMessage.objects.create(ticket=t, sender=request.user, is_admin=False, message=message)
        messages.success(request, 'Ticket submitted. We will reply via this page and email.')
        return redirect('ticket_detail', ticket_id=t.id)
    return render(request, 'freshbread/tickets/new.html')


@login_required
def ticket_detail(request, ticket_id: int):
    t = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    if request.method == 'POST' and t.status != 'closed':
        action = request.POST.get('action')
        if action == 'close':
            t.status = 'closed'
            t.closed_at = timezone.now()
            t.closed_by = request.user
            t.save(update_fields=['status', 'closed_at', 'closed_by'])
            messages.info(request, 'Ticket closed.')
            return redirect('ticket_detail', ticket_id=t.id)
        msg = (request.POST.get('message') or '').strip()
        if msg:
            TicketMessage.objects.create(ticket=t, sender=request.user, is_admin=False, message=msg)
            t.status = 'open'
            t.save(update_fields=['status'])
            messages.success(request, 'Message sent.')
            return redirect('ticket_detail', ticket_id=t.id)
    msgs = t.messages.order_by('created_at')
    return render(request, 'freshbread/tickets/detail.html', {"ticket": t, "messages": msgs})


@login_required
@admin_login_protect
def admin_tickets(request):
    qs = SupportTicket.objects.all().order_by('-updated_at')
    return render(request, 'freshbread/admin/tickets.html', {"tickets": qs})


@login_required
@admin_login_protect
def admin_ticket_detail(request, ticket_id: int):
    t = get_object_or_404(SupportTicket, id=ticket_id)
    if request.method == 'POST' and t.status != 'closed':
        action = request.POST.get('action')
        if action == 'close':
            t.status = 'closed'
            t.closed_at = timezone.now()
            t.closed_by = request.user
            t.save(update_fields=['status', 'closed_at', 'closed_by'])
            messages.info(request, 'Ticket closed.')
            return redirect('admin_ticket_detail', ticket_id=t.id)
        msg = (request.POST.get('message') or '').strip()
        if msg:
            TicketMessage.objects.create(ticket=t, sender=request.user, is_admin=True, message=msg)
            t.status = 'answered'
            t.save(update_fields=['status'])
            try:
                if t.user.email:
                    email_sender.send(
                        subject='Your support ticket was answered',
                        message=f'Your ticket "{t.subject}" has a new reply.',
                        to=t.user.email,
                        html_message=f'<p>Your ticket "{t.subject}" has a new reply.</p>',
                        wrap=True,
                    )
            except Exception:
                pass
            messages.success(request, 'Reply sent.')
            return redirect('admin_ticket_detail', ticket_id=t.id)
    msgs = t.messages.order_by('created_at')
    return render(request, 'freshbread/admin/ticket_detail.html', {"ticket": t, "messages": msgs, "user": t.user})