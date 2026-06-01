from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from core.interfaces.http.decorators import admin_login_protect
from core.infrastructure.models import ReleaseNote


@admin_login_protect
def admin_releases(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create":
            version = (request.POST.get("version") or "").strip()
            release_date = (request.POST.get("release_date") or "").strip()
            features = (request.POST.get("features") or "").strip()
            bug_fixes = (request.POST.get("bug_fixes") or "").strip()
            published = request.POST.get("published") == "on"
            if not version or not release_date:
                messages.error(request, "Version and release date are required.")
            else:
                try:
                    dt = timezone.datetime.fromisoformat(release_date).date()
                except Exception:
                    messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
                    return redirect("admin_releases")
                ReleaseNote.objects.create(
                    version=version,
                    release_date=dt,
                    features=features,
                    bug_fixes=bug_fixes,
                    published=published,
                )
                messages.success(request, "Release created.")
            return redirect("admin_releases")
        if action == "toggle":
            rid = request.POST.get("id")
            obj = ReleaseNote.objects.filter(id=rid).first()
            if obj:
                obj.published = not obj.published
                obj.save(update_fields=["published"])
                messages.success(request, "Release publication updated.")
            return redirect("admin_releases")
        if action == "delete":
            rid = request.POST.get("id")
            ReleaseNote.objects.filter(id=rid).delete()
            messages.success(request, "Release deleted.")
            return redirect("admin_releases")
    releases = ReleaseNote.objects.all()[:20]
    return render(request, "freshbread/admin/releases.html", {"releases": releases})
