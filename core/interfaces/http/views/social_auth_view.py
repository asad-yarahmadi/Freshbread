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
    if not request.user.is_authenticated:
        messages.error(request, "Social login failed ⚠️")
        return redirect("ru")

    email = request.user.email
    if not email:
        messages.error(request, "No email found ⚠️")
        return redirect("ru")

    provider = getattr(request.user.social_auth.first(), "provider", "unknown")

    profile, created = SocialProfile.objects.get_or_create(
        email=email,
        defaults={"provider": provider}
    )

    if profile.user and profile.profile_completed and profile.acc_prpo:
        login(request, profile.user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect("index")

    logout(request)
    request.session['social_email'] = profile.email
    request.session['social_provider'] = provider
    return redirect("complete_social_profile_view")
