"""
Authentication Domain Entities
Entityهای مربوط به احراز هویت کاربران
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from django.contrib.auth.models import User


@dataclass
class AuthEntity:
    """
    Entity اصلی برای عملیات احراز هویت
    """
    user: Optional[User] = None
    username_or_email: str = ""
    password: str = ""
    ip_address: str = ""
    is_authenticated: bool = False
    session_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.session_data is None:
            self.session_data = {}

    def validate_credentials(self) -> bool:
        """
        اعتبارسنجی اولیه credentials
        """
        if not self.username_or_email or not self.password:
            return False
        return len(self.password) >= 6

    def is_banned(self) -> bool:
        """
        بررسی وضعیت ban کاربر
        """
        if not self.user:
            return False
        return not self.user.is_active

    def get_user_info(self) -> Dict[str, Any]:
        """
        دریافت اطلاعات کاربر
        """
        if not self.user:
            return {}

        return {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
            'is_active': self.user.is_active,
            'date_joined': self.user.date_joined,
            'last_login': self.user.last_login,
        }


@dataclass
class SignupEntity:
    """
    Entity برای عملیات ثبت نام
    """
    username: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    first_name: str = ""
    last_name: str = ""
    ip_address: str = ""
    verification_code: str = ""

    def validate_basic_info(self) -> bool:
        """
        اعتبارسنجی اطلاعات پایه
        """
        if not all([self.username, self.email, self.password, self.confirm_password]):
            return False

        if self.password != self.confirm_password:
            return False

        if len(self.password) < 6:
            return False

        return True

    def get_user_data(self) -> Dict[str, Any]:
        """
        دریافت داده‌های کاربر برای ایجاد
        """
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }


@dataclass
class ProfileEntity:
    """
    Entity برای پروفایل کاربر
    """
    user: Optional[User] = None
    phone: str = ""
    address: str = ""
    city: str = ""
    profile_image = None
    is_complete: bool = False

    def is_profile_complete(self) -> bool:
        """
        بررسی کامل بودن پروفایل
        """
        required_fields = [self.phone, self.address, self.city]
        return all(required_fields) and bool(self.user)

    def get_profile_data(self) -> Dict[str, Any]:
        """
        دریافت داده‌های پروفایل
        """
        if not self.user:
            return {}

        return {
            'user_id': self.user.id,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'profile_image': self.profile_image,
            'is_complete': self.is_complete,
        }


@dataclass
class OAuthEntity:
    """
    Entity برای OAuth authentication
    """
    provider: str = ""
    access_token: str = ""
    user_info: Dict[str, Any] = None
    email: str = ""
    name: str = ""

    def __post_init__(self):
        if self.user_info is None:
            self.user_info = {}

    def is_valid_oauth_data(self) -> bool:
        """
        اعتبارسنجی داده‌های OAuth
        """
        return bool(self.access_token and self.email)

    def get_user_data(self) -> Dict[str, Any]:
        """
        دریافت داده‌های کاربر از OAuth
        """
        return {
            'email': self.email,
            'first_name': self.name.split()[0] if self.name else '',
            'last_name': ' '.join(self.name.split()[1:]) if self.name and len(self.name.split()) > 1 else '',
            'oauth_provider': self.provider,
            'oauth_data': self.user_info,
        }


@dataclass
class PasswordResetEntity:
    """
    Entity برای بازنشانی رمز عبور
    """
    email: str = ""
    reset_token: str = ""
    new_password: str = ""
    confirm_password: str = ""

    def validate_reset_request(self) -> bool:
        """
        اعتبارسنجی درخواست بازنشانی
        """
        return bool(self.email)

    def validate_new_password(self) -> bool:
        """
        اعتبارسنجی رمز عبور جدید
        """
        if not all([self.new_password, self.confirm_password]):
            return False

        if self.new_password != self.confirm_password:
            return False

        return len(self.new_password) >= 6