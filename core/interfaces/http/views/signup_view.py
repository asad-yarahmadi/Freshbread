from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from urllib.parse import urlparse

def signup_view(request):
    # Lazy imports to avoid early app loading issues
    from core.application.services.signup_service import signup_service
    from core.application.security.ddos_checker import ddos_checker
    from core.interfaces.http.utils.ip import get_client_ip
    from core.application.security.suspicious_recorder import mark_form_render, record_failure

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
            # Delegate to application service with request/session data
            signup_service.start(
                username=request.POST.get("username"),
                email=request.POST.get("email"),
                password=request.POST.get("password"),
                password_confirm=request.POST.get("password_confirm"),
                acc_prpo=request.POST.get("acc_prpo") == "on",
                ip=get_client_ip(request),
                request=request,   # برای session
            )
            if next_url:
                request.session['next_url'] = next_url
            return render(request, "freshbread/verify_email.html", {"next": next_url})

        except Exception as e:
            uname = (request.POST.get("username") or "").strip()
            mail = (request.POST.get("email") or "").strip()
            record_failure(request, "signup_failed", meta_text=f"user={uname} email={mail}")
            messages.error(request, str(e))

    mark_form_render(request, "signup_failed")
    return render(request, "freshbread/signup/su.html", {"next": next_url})
