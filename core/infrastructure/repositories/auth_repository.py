"""
Authentication Repository
ONLY database operations
"""
from typing import Optional, Dict, Any
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from core.infrastructure.models import LoginAttempt, TempUser, Profile


class AuthRepository:

    # ---------- USER ----------

    @staticmethod
    def get_user_by_username_or_email(value: str) -> Optional[User]:
        if "@" in value:
            return User.objects.filter(email__iexact=value).first()
        return User.objects.filter(username__iexact=value).first()

    @staticmethod
    def create_user(data: Optional[Dict[str, Any]] = None, **kwargs) -> User:
        if data is not None:
            return User.objects.create_user(**data)
        return User.objects.create_user(**kwargs)

    @staticmethod
    def activate_user(user: User):
        user.is_active = True
        user.save(update_fields=["is_active"])

    # ---------- TEMP USER ----------

    @staticmethod
    def create_temp_user(**kwargs) -> TempUser:
        return TempUser.objects.create(**kwargs)

    @staticmethod
    def get_temp_user(email: str) -> Optional[TempUser]:
        return TempUser.objects.filter(email__iexact=email).first()

    @staticmethod
    def delete_temp_user(temp_user: TempUser):
        temp_user.delete()

    # ---------- PROFILE ----------

    @staticmethod
    def get_profile(user: User) -> Optional[Profile]:
        return Profile.objects.filter(user=user).first()

    @staticmethod
    def save_profile(profile: Profile):
        profile.save()

    # ---------- LOGIN ATTEMPT ----------

    @staticmethod
    def log_attempt(user, ip: str, success: bool):
        return LoginAttempt.objects.create(
            user=user,
            ip_address=ip,
        )

    @staticmethod
    def log_login_attempt(user, ip: str, success: bool):
        return LoginAttempt.objects.create(
            user=user,
            ip_address=ip,
        )

    @staticmethod
    def is_ip_banned(ip: str) -> bool:
        return LoginAttempt.objects.filter(
            ip_address=ip,
            blocked_until__gt=timezone.now()
        ).exists()

    @staticmethod
    def ban_ip(ip: str, minutes: int):
        LoginAttempt.objects.create(
            ip_address=ip,
            blocked_until=timezone.now() + timedelta(minutes=minutes)
        )

    # ---------- HELPERS ----------
    @staticmethod
    def update_user_last_login(user: User, ip: str):
        from core.infrastructure.models import Profile
        profile = Profile.objects.filter(user=user).first()
        if profile:
            profile.last_login_ip = ip
            profile.save(update_fields=["last_login_ip"])

    @staticmethod
    def get_temp_user_by_email(email: str) -> Optional[TempUser]:
        return TempUser.objects.filter(email__iexact=email).first()
