from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User

from core.interfaces.http.decorators import admin_login_protect
from core.infrastructure.models import BlogPost, AdminNotification
from core.infrastructure.email.email_sender import email_sender


@admin_login_protect
def admin_users(request):
    q = (request.GET.get("q") or "").strip()
    users = User.objects.all().order_by("-date_joined")
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    return render(request, "freshbread/admin/users.html", {"users": users, "q": q})


@admin_login_protect
def admin_user_detail(request, user_id: int):
    target = get_object_or_404(User, pk=user_id)
    profile = getattr(target, "profile", None)
    blogs = BlogPost.objects.filter(author=target).order_by("-created_at")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "activate":
            target.is_active = True
            target.save(update_fields=["is_active"])
            messages.success(request, "User activated.")

        elif action == "deactivate":
            target.is_active = False
            target.save(update_fields=["is_active"])
            messages.success(request, "User deactivated.")

        elif action == "ban":
            target.is_active = False
            target.save(update_fields=["is_active"])
            if profile:
                profile.acc_prpo = False
                profile.save(update_fields=["acc_prpo"])
            try:
                if target.email:
                    email_sender.send(
                        subject="Account status updated",
                        message="Your account has been banned by admin.",
                        to=target.email,
                    )
            except Exception:
                pass
            AdminNotification.objects.create(
                user=target,
                message="Your account has been banned by admin.",
                url="/",
            )
            messages.success(request, "User banned.")

        elif action == "delete_account":
            username = target.username
            try:
                target.delete()
                messages.success(request, f"Account '{username}' deleted.")
                return redirect("admin_users")
            except Exception:
                messages.error(request, "Failed to delete account.")

        elif action == "delete_blog":
            slug = request.POST.get("slug")
            if slug:
                post = BlogPost.objects.filter(slug=slug, author=target).first()
                if post:
                    title = post.title
                    post.delete()
                    AdminNotification.objects.create(
                        user=target,
                        message=f"Your blog '{title}' was removed by admin.",
                        url="/blog/",
                    )
                    try:
                        if target.email:
                            email_sender.send(
                                subject="Blog removed",
                                message=f"Your blog '{title}' was removed by admin.",
                                to=target.email,
                            )
                    except Exception:
                        pass
                    messages.success(request, "Blog deleted and user notified.")
                else:
                    messages.error(request, "Blog not found.")

        elif action == "save_note":
            note = (request.POST.get("admin_note") or "").strip()
            if profile is not None:
                profile.admin_note = note
                profile.save(update_fields=["admin_note"])
                messages.success(request, "Admin note saved.")
            else:
                messages.error(request, "Profile not found.")

        elif action == "send_email":
            subject = (request.POST.get("subject") or "").strip()
            body = (request.POST.get("body") or "").strip()
            if not subject or not body:
                messages.error(request, "Subject and body are required.")
            else:
                try:
                    if target.email:
                        email_sender.send(subject=subject, message=body, to=target.email)
                        messages.success(request, "Email sent.")
                    else:
                        messages.error(request, "User has no email.")
                except Exception:
                    messages.error(request, "Failed to send email.")

        return redirect("admin_user_detail", user_id=target.id)

    ctx = {
        "target": target,
        "profile": profile,
        "blogs": blogs,
    }
    return render(request, "freshbread/admin/user_detail.html", ctx)