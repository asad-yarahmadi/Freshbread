from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from core.infrastructure.models import SupportTicket, TicketMessage
from core.infrastructure.email.email_sender import email_sender
from core.interfaces.http.decorators import admin_login_protect

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