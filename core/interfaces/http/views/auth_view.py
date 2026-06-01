from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


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
            return redirect("index")
        except Exception as e:
            username = (request.POST.get("username") or "").strip()
            record_failure(request, "login_failed", meta_text=f"user={username}")
            messages.error(request, str(e))
            return redirect("ru")

    mark_form_render(request, "login_failed")
    return render(request, "freshbread/auth/ru.html")


@login_required
def logout_view(request):
    # Lazy import to ensure services load after apps
    from core.application.services.auth_service import auth_service

    auth_service.logout(request)
    messages.success(request, "✅ You have been logged out successfully.")
    return redirect("index")
