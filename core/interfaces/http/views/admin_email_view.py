from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.conf import settings

def _render_body(template: str, user: User) -> str:
    vals = {
        "username": user.username or "",
        "user_name": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "action_url": getattr(settings, "SITE_URL", "/"),
    }
    body = template or ""
    for k, v in vals.items():
        body = body.replace("{" + k + "}", v)
        body = body.replace("{{ " + k + " }}", v)
    return body

@login_required
def admin_email(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect("index")
    from core.infrastructure.models.scheduled_email import ScheduledEmail
    scheduled = ScheduledEmail.objects.filter(is_active=True).order_by("-created_at")

    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        body_template = request.POST.get("body", "").strip()
        audience = request.POST.get("audience", "all")
        repeat = request.POST.get("repeat", "none")
        interval_days = request.POST.get("interval_days")
        interval_days = int(interval_days) if interval_days and interval_days.isdigit() else None
        send_now = request.POST.get("send_now") == "1"

        if not subject or not body_template:
            messages.error(request, "Subject and body are required.")
            return render(request, "freshbread/admin_email.html", {"scheduled": scheduled})

        # resolve recipients
        qs = User.objects.all()
        if audience == "admins":
            qs = qs.filter(is_staff=True)
        elif audience == "users":
            qs = qs.filter(is_staff=False)
        recipients = [u.email for u in qs if u.email]

        if send_now and recipients:
            try:
                from core.infrastructure.email.email_sender import email_sender
                for u in qs:
                    if not u.email:
                        continue
                    body = _render_body(body_template, u)
                    email_sender.send(subject=subject, message=strip_tags(body), html_message=body, to=u.email)
                messages.success(request, "Email(s) sent.")
            except Exception:
                messages.error(request, "Failed to send emails.")

        # schedule if repeat selected
        next_run = None
        if repeat != "none":
            now = timezone.now()
            if repeat == "daily":
                next_run = now + timezone.timedelta(days=1)
            elif repeat == "weekly":
                next_run = now + timezone.timedelta(weeks=1)
            elif repeat == "monthly":
                next_run = now + timezone.timedelta(days=30)
            elif repeat == "custom" and interval_days:
                next_run = now + timezone.timedelta(days=interval_days)
            ScheduledEmail.objects.create(
                creator=request.user,
                subject=subject,
                body_template=body_template,
                audience=audience,
                repeat=repeat,
                interval_days=interval_days,
                next_run_at=next_run,
                is_active=True,
            )
            messages.success(request, "Scheduled email saved.")

        scheduled = ScheduledEmail.objects.filter(is_active=True).order_by("-created_at")
        return render(request, "freshbread/admin_email.html", {"scheduled": scheduled})

    return render(request, "freshbread/admin_email.html", {"scheduled": scheduled})