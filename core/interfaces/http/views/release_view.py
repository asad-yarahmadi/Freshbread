from django.shortcuts import render, get_object_or_404
from core.infrastructure.models import ReleaseNote


def releases_list(request):
    releases = ReleaseNote.objects.filter(published=True).order_by("-release_date", "-created_at")
    return render(request, "freshbread/releases/list.html", {"releases": releases})


def release_detail(request, version):
    release = get_object_or_404(ReleaseNote, version=version, published=True)
    return render(request, "freshbread/releases/detail.html", {"release": release})
