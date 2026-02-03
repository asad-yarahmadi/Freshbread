from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

def verify_email_view(request):
    # Lazy imports to prevent early app loading
    from core.application.services.email_verification_service import email_verification_service
    from core.application.security.ddos_checker import ddos_checker

    # session check: allow either signup or email-change flow
    has_signup = all([
        request.session.get("signup_username"),
        request.session.get("signup_email"),
        request.session.get("signup_password"),
    ])
    has_email_change = bool(request.session.get("email_change_user_id"))
    if not (has_signup or has_email_change):
        messages.error(request, "⚠️ Session expired. Please start again.")
        return redirect("index")

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        code = request.POST.get("code", "").strip()
        try:
            result = email_verification_service.handle(
                request=request,
                action=action,
                code=code
            )
            if result == "verified_signup":
                return redirect("complete_profile")
            elif result == "verified_email_change":
                messages.success(request, "Email verified. Changes applied.")
                return redirect("profile")
            else:
                messages.success(request, "Verification code resent.")
                return redirect("verify_email")

        except Exception as e:
            messages.error(request, str(e))
            return redirect("verify_email")

    return render(request, "freshbread/verify_email.html")
