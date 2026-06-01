from django.shortcuts import render, redirect
from django.contrib import messages

from core.interfaces.http.decorators import admin_login_protect
from core.infrastructure.models import SiteAnnouncement


@admin_login_protect
def admin_announcements(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            title = (request.POST.get("title") or "").strip()
            body = (request.POST.get("body") or "").strip()
            is_active = request.POST.get("is_active") == "on"
            show_once = request.POST.get("show_once") == "on"
            if not title or not body:
                messages.error(request, "Title and body are required.")
            else:
                SiteAnnouncement.objects.create(
                    title=title,
                    body=body,
                    is_active=is_active,
                    show_once=show_once,
                )
                messages.success(request, "Announcement created.")
            return redirect("admin_announcements")
        if action == "toggle":
            aid = request.POST.get("id")
            obj = SiteAnnouncement.objects.filter(id=aid).first()
            if obj:
                obj.is_active = not obj.is_active
                obj.save(update_fields=["is_active"])
                messages.success(request, "Announcement status updated.")
            return redirect("admin_announcements")
        if action == "delete":
            aid = request.POST.get("id")
            SiteAnnouncement.objects.filter(id=aid).delete()
            messages.success(request, "Announcement deleted.")
            return redirect("admin_announcements")
    anns = SiteAnnouncement.objects.order_by("-created_at")[:20]
    return render(request, "freshbread/admin/announcements.html", {"announcements": anns})
