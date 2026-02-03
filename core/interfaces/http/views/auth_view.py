from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    # Lazy imports to avoid AppRegistry issues during startup
    from core.application.services.auth_service import auth_service
    from core.application.security.ddos_checker import ddos_checker
    from core.interfaces.http.utils.ip import get_client_ip

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    if request.method == "POST":
        try:
            # Call application service through DDD interface
            auth_service.login(
                request=request,
                username_or_email=request.POST.get("username", ""),
                password=request.POST.get("password", ""),
                ip=get_client_ip(request)
            )
            return redirect("index")
        except Exception as e:
            messages.error(request, str(e))
            return redirect("ru")

    return render(request, "freshbread/auth/ru.html")


@login_required
def logout_view(request):
    # Lazy import to ensure services load after apps
    from core.application.services.auth_service import auth_service

    auth_service.logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect("index")
