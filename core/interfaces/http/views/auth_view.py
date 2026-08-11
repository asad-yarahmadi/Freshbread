from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlparse


def login_view(request):
    # Lazy imports to avoid AppRegistry issues during startup
    from core.application.services.auth_service import auth_service
    from core.application.security.ddos_checker import ddos_checker
    from core.interfaces.http.utils.ip import get_client_ip
    from core.application.security.suspicious_recorder import mark_form_render, record_failure, record_success
    from django.contrib.auth import get_user_model

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    next_url = request.GET.get('next', '')
    if next_url:
        parsed_next = urlparse(next_url)
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            next_url = ''

    if request.method == "POST":
        try:
            # Call application service through DDD interface
            auth_service.login(
                request=request,
                username_or_email=request.POST.get("username", ""),
                password=request.POST.get("password", ""),
                ip=get_client_ip(request)
            )
            try:
                User = get_user_model()
                identifier = (request.POST.get("username") or "").strip()
                user_obj = None
                if identifier:
                    try:
                        user_obj = User.objects.filter(username=identifier).first()
                        if not user_obj:
                            user_obj = User.objects.filter(email=identifier).first()
                    except Exception:
                        user_obj = None
                record_success(request, "login_success", user=user_obj, status_code=200)
            except Exception:
                pass
            next_url_post = request.POST.get('next', '')
            if next_url_post:
                parsed_next = urlparse(next_url_post)
                if url_has_allowed_host_and_scheme(next_url_post, allowed_hosts={request.get_host()}):
                    return redirect(next_url_post)
            return redirect("index")
        except Exception as e:
            username = (request.POST.get("username") or "").strip()
            record_failure(request, "login_failed", meta_text=f"user={username}")
            messages.error(request, str(e))
            redirect_url = f"ru?next={next_url}" if next_url else "ru"
            return redirect(redirect_url)

    mark_form_render(request, "login_failed")
    return render(request, "freshbread/auth/ru.html", {"next": next_url})


@login_required
def logout_view(request):
    # Lazy import to ensure services load after apps
    from core.application.services.auth_service import auth_service

    auth_service.logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect("index")
