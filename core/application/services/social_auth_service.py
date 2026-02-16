from django.core.exceptions import ValidationError
from django.contrib.auth import login, logout
from django.contrib.auth.models import User

from core.domain.validators.name_validators import validate_name
from core.infrastructure.models import SocialProfile
import re
import requests


class SocialAuthService:

    def check_profile(self, request):
        if not request.user.is_authenticated:
            raise ValidationError("Social login failed ⚠️")

        email = request.user.email
        if not email:
            raise ValidationError("No email found ⚠️")

        provider = getattr(
            request.user.social_auth.first(),
            "provider",
            "unknown"
        )

        profile, _ = SocialProfile.objects.get_or_create(
            email=email,
            defaults={"provider": provider}
        )

        # Link SocialProfile to existing user to avoid duplicate accounts
        if not profile.user:
            u = request.user
            if not getattr(u, "email", None):
                u = User.objects.filter(email__iexact=email).first()
            if u:
                profile.user = u
                profile.save(update_fields=["user"]) 

        # If the linked user's regular Profile is already complete, skip social form
        if profile.user:
            from core.infrastructure.models import Profile as UserProfile
            up = UserProfile.objects.filter(user=profile.user).first()
            if up and up.profile_completed and up.acc_prpo:
                login(request, profile.user, backend='django.contrib.auth.backends.ModelBackend')
                return "index"

        logout(request)
        request.session["social_email"] = profile.email
        request.session["social_provider"] = provider
        return "complete_social_profile_view"

    def complete_profile(self, *, request, data):
        email = request.session.get("social_email")
        provider = request.session.get("social_provider", "unknown")

        if not email:
            raise ValidationError("Session expired ⚠️ Please login again.")

        try:
            profile = SocialProfile.objects.get(email=email)
        except SocialProfile.DoesNotExist:
            raise ValidationError("Profile not found ⚠️")

        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()

        if not first_name or not last_name or not data.get("acc_prpo"):
            raise ValidationError("Please complete all required fields ⚠️")

        validate_name(first_name)
        validate_name(last_name)

        if not profile.user:
            username_base = email.split("@")[0]
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
            user = User.objects.create(username=username, email=email)
            profile.user = user
        else:
            user = profile.user

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # location moved to multi-location manager; skip map validation here

        profile.profile_completed = True
        profile.acc_prpo = True
        profile.provider = provider
        profile.phone = data.get("phone")
        # do not set coordinates here; handled via UserLocation manager
        profile.save()

        # sync to regular Profile used by pfe
        from core.infrastructure.models import Profile as UserProfile
        up, _ = UserProfile.objects.get_or_create(user=user)
        up.phone = profile.phone
        # location fields managed via UserLocation entries
        up.profile_completed = True
        up.acc_prpo = True
        up.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        code = (request.POST.get("referral_code") or "").strip().upper()
        if code:
            from core.infrastructure.models import Profile as UserProfile
            from core.infrastructure.models import ReferralRecord
            owner_profile = UserProfile.objects.filter(referral_code=code).first()
            if owner_profile and owner_profile.user != user:
                ReferralRecord.objects.get_or_create(owner=owner_profile.user, used_by=user)


social_auth_service = SocialAuthService()
