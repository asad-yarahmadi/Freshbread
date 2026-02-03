from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from core.domain.validators.name_validators import validate_name
from core.interfaces.http.utils.ip import get_client_ip


class ProfileService:

    def complete_profile_after_signup(self, *, request, first_name: str, last_name: str):
        from core.infrastructure.models import Profile
        from core.infrastructure.models import ReferralRecord
        username = request.session.get("signup_username")
        email = request.session.get("signup_email")
        password = request.session.get("signup_password")

        if not all([username, email, password]):
            raise ValidationError("⚠️ Session expired. Please register again.")

        validate_name(first_name)
        validate_name(last_name)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        Profile.objects.create(
            user=user,
            signup_ip=get_client_ip(request),
            acc_prpo=True
        )

        code = (request.POST.get("referral_code") or "").strip().upper()
        if code:
            from core.infrastructure.models import Profile as UserProfile
            owner_profile = UserProfile.objects.filter(referral_code=code).first()
            if owner_profile and owner_profile.user != user:
                ReferralRecord.objects.get_or_create(owner=owner_profile.user, used_by=user)

        for key in ("signup_username", "signup_email", "signup_password"):
            request.session.pop(key, None)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')


profile_service = ProfileService()
