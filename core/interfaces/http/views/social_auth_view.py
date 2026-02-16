from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import login, logout
from core.infrastructure.models import SocialProfile
from core.application.security.ddos_checker import ddos_checker
def oauth_google_view(request):
    return redirect('/oauth_google/login/google-oauth2/')



def complete_social_profile_view(request):
    # Lazy import
    from core.application.services.social_auth_service import social_auth_service

    try:
        if request.method == "POST":
            social_auth_service.complete_profile(
                request=request,
                data=request.POST
            )
            messages.success(request, "Profile completed successfully ✅")
            return redirect("profile")

        return render(request, "freshbread/social_auth/complete_profile1.html", {
            "email": request.session.get("social_email"),
            "provider": request.session.get("social_provider"),
        })

    except Exception as e:
        messages.error(request, str(e))
        return redirect("ru")

def check_social_profile_view(request):
    blocked = ddos_checker.check(request)
    if blocked:
        return blocked
    from core.application.services.social_auth_service import social_auth_service
    try:
        target = social_auth_service.check_profile(request)
        return redirect(target)
    except Exception as e:
        messages.error(request, str(e))
        return redirect("ru")
