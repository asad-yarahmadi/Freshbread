from django.contrib import admin
from django.urls import path, include
from django.conf.urls import handler404, handler500, handler403
from django.shortcuts import render

# -------------------------
# Handlers
# -------------------------

def handler404(request, exception):
    return render(request, "freshbread/errors/404.html", status=404)

def handler403(request, exception=None):
    return render(request, "freshbread/errors/403.html", status=403)

def handler500 (request):
    return render(request, "freshbread/errors/500.html", status=500)