from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.db import IntegrityError

from core.domain.validators.user_validators import validate_username
from core.domain.utils.verification import generate_verification_code
from core.infrastructure.email.email_sender import email_sender
from django.contrib.auth.models import User
from core.infrastructure.models import TempUser, Profile


class SignupService:

    def start(self, *, username, email, password, password_confirm, acc_prpo, ip, request):
        # username
        validate_username(username)

        # email
        validate_email(email)

        # password
        validate_password(password)
        if password != password_confirm:
            raise ValidationError("Passwords do not match.")

        if not acc_prpo:
            raise ValidationError("You must accept the privacy policy.")

        # IP limit (business rule)
        threshold = timezone.now() - timedelta(hours=30)
        if Profile.objects.filter(signup_ip=ip, user__date_joined__gte=threshold).count() >= 5:
            raise ValidationError("You can only register 5 times every 30 hours from the same IP.")

        # duplicates
        if User.objects.filter(username=username).exists():
            raise ValidationError("Username already exists.")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists.")

        # cleanup old temp users
        TempUser.objects.filter(username=username).delete()
        TempUser.objects.filter(email=email).delete()

        # create temp user
        code = generate_verification_code()
        expires = timezone.now() + timedelta(minutes=2)

        try:
            TempUser.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                acc_prpo=acc_prpo,
                ip=ip,
                verification_code=code,
                expires_at=expires,
            )
        except IntegrityError:
            raise ValidationError("Username or email already exists.")

        # send email (HTML + text)
        try:
            from django.urls import reverse
            action_url = request.build_absolute_uri(reverse('verify_email'))
        except Exception:
            action_url = ""
        email_sender.send(
            subject="🔐 Verify Your Email",
            message=(
                f"Hello {username},\n\n"
                f"Verification Code: {code}\n\n"
                "This code will expire in 2 minutes."
            ),
            to=email,
            html_message=(
                f"Hi {username},<br>"
                "Thanks for signing up for Kingfood. Please confirm your email address to secure your account and start enjoying fresh-baked goodness every day.<br><br>"
                f"Verification Code: <strong>{code}</strong>"
            ),
            title="Confirm Your Email",
            cta_text="Verify Email",
            action_url=action_url,
            wrap=True,
        )

        # session
        request.session["signup_username"] = username
        request.session["signup_email"] = email
        request.session["signup_password"] = password


signup_service = SignupService()
