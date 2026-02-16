from django.shortcuts import render, redirect
from django.contrib import messages

def signup_view(request):
    # Lazy imports to avoid early app loading issues
    from core.application.services.signup_service import signup_service
    from core.application.security.ddos_checker import ddos_checker
    from core.interfaces.http.utils.ip import get_client_ip

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

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
            return render(request, "freshbread/verify_email.html")

        except Exception as e:
            messages.error(request, str(e))

    return render(request, "freshbread/signup/su.html")
