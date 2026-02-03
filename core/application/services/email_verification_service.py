from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

from core.domain.utils.verification import generate_verification_code
from core.infrastructure.models import TempUser, Profile
from core.infrastructure.email.email_sender import email_sender


class EmailVerificationService:

    MAX_ATTEMPTS = 3
    EXPIRY_MINUTES = 2

    def handle(self, *, request, action: str, code: str):
        now = timezone.now()

        is_email_change = bool(request.session.get("email_change_user_id"))
        if is_email_change:
            user_id = request.session.get("email_change_user_id")
            email = request.session.get("email_change_new_email")
            if not (user_id and email):
                raise ValidationError("Session expired ⚠️ Please try again.")
            username = f"emailchange_{user_id}"
            temp_user, _ = TempUser.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "password": "",
                    "verification_code": generate_verification_code(),
                    "expires_at": now + timedelta(minutes=self.EXPIRY_MINUTES),
                    "is_verified": False,
                    "failed_attempts": 0,
                }
            )
            if temp_user.email != email:
                temp_user.email = email
                temp_user.save(update_fields=["email"])
        else:
            username = request.session["signup_username"]
            email = request.session["signup_email"]
            try:
                temp_user = TempUser.objects.get(
                    username=username,
                    email=email,
                    is_verified=False
                )
            except TempUser.DoesNotExist:
                raise ValidationError("Temporary user not found. Please register again.")

        # IP limit (business rule)
        ip = request.META.get("REMOTE_ADDR")
        threshold = now - timedelta(hours=30)
        if Profile.objects.filter(
            signup_ip=ip,
            user__date_joined__gte=threshold
        ).count() >= 5:
            raise ValidationError("🚫 Too many registrations from this IP.")

        # ======================
        # RESEND CODE
        # ======================
        if action == "resend":
            if temp_user.expires_at and now < temp_user.expires_at:
                remaining = int((temp_user.expires_at - now).total_seconds())
                raise ValidationError(
                    f"⏳ Please wait {remaining // 60}m {remaining % 60}s."
                )

            new_code = generate_verification_code()
            temp_user.verification_code = new_code
            temp_user.expires_at = now + timedelta(minutes=self.EXPIRY_MINUTES)
            temp_user.failed_attempts = 0
            temp_user.save()

            email_sender.send(
                subject="🔁 Resent Verification Code",
                message=f"Your verification code is: {new_code}",
                to=email
            )
            return "resent"

        # ======================
        # VERIFY CODE
        # ======================
        if action == "verify":
            if not temp_user.expires_at or now > temp_user.expires_at:
                temp_user.delete()
                raise ValidationError("⏳ Verification code expired. Please register again.")

            if temp_user.verification_code.lower() != code.lower():
                temp_user.failed_attempts += 1
                temp_user.save()

                if temp_user.failed_attempts >= self.MAX_ATTEMPTS:
                    temp_user.delete()
                    raise ValidationError("🚫 Too many wrong attempts. Please register again.")

                remaining = self.MAX_ATTEMPTS - temp_user.failed_attempts
                raise ValidationError(f"❌ Invalid code. {remaining} attempts left.")

            # success
            temp_user.is_verified = True
            temp_user.save()
            if is_email_change:
                # apply pending changes
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=request.session.get("email_change_user_id"))
                except User.DoesNotExist:
                    raise ValidationError("User not found.")
                payload = request.session.get("email_change_payload", {})
                user.email = request.session.get("email_change_new_email")
                if payload.get("first_name"):
                    user.first_name = payload["first_name"]
                if payload.get("last_name"):
                    user.last_name = payload["last_name"]
                user.save()

                profile = Profile.objects.filter(user=user).first()
                if profile:
                    for key in ("phone", "postal_code", "latitude", "longitude"):
                        if key in payload and payload[key] is not None:
                            setattr(profile, key, payload[key])
                    profile.save()

                # cleanup
                for k in ("email_change_user_id", "email_change_new_email", "email_change_payload"):
                    request.session.pop(k, None)
                return "verified_email_change"
            else:
                try:
                    from django.urls import reverse
                    action_url = request.build_absolute_uri(reverse('index'))
                except Exception:
                    action_url = request.build_absolute_uri('/') if hasattr(request, 'build_absolute_uri') else ''
                # Send welcome email
                email_sender.send(
                    subject="Welcome",
                    message=f"Welcome, {request.session.get('signup_username', '')}!",
                    to=temp_user.email,
                    html_message=(
                        f"Hi {request.session.get('signup_username', '')},<br>"
                        "Your email was successfully verified. Welcome to Fresh Bread Bakery! Explore daily specials, schedule pickups, and enjoy warm, freshly baked bread made with care."
                    ),
                    title="Welcome to Fresh Bread Bakery",
                    cta_text="Get Started",
                    action_url=action_url,
                    wrap=True,
                )
                return "verified_signup"

        raise ValidationError("⚠️ Invalid action.")


email_verification_service = EmailVerificationService()
