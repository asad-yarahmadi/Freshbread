from django.shortcuts import redirect
from django.urls import reverse


def save_email_provider(backend, user, response, *args, **kwargs):
    """
    Social Auth Pipeline: Save email and provider from OAuth backends.
    
    This function is called during the social authentication process.
    It extracts the email from different OAuth providers (GitHub, Google, Facebook)
    and saves it to the session for later use.
    """
    request = backend.strategy.request
    email = None

    if backend.name == "github":
        email = response.get("email")
        # گیت‌هاب بعضی وقتا ایمیل رو مستقیم نمیده → باید از extra_data گرفت
        if not email and hasattr(user, "email"):
            email = user.email

    elif backend.name == "google-oauth2":
        email = response.get("email")

    elif backend.name == "facebook":
        email = response.get("email")

    if email:
        request.session["social_email"] = email
        request.session["social_provider"] = backend.name
