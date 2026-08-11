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
    from django.utils.http import url_has_allowed_host_and_scheme
    from urllib.parse import urlparse

    next_url = request.session.get('next_url', '')

    try:
        if request.method == "POST":
            social_auth_service.complete_profile(
                request=request,
                data=request.POST
            )
            messages.success(request, "Profile completed successfully ✅")
            if next_url:
                parsed_next = urlparse(next_url)
                if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    if 'next_url' in request.session:
                        del request.session['next_url']
                    return redirect(next_url)
            return redirect("profile")

        return render(request, "freshbread/social_auth/complete_profile1.html", {
            "email": request.session.get("social_email"),
            "provider": request.session.get("social_provider"),
            "next": next_url
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
