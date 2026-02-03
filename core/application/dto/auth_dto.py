"""
Authentication DTOs
Data Transfer Objects برای عملیات احراز هویت
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class LoginDTO:
    """
    DTO برای درخواست ورود
    """
    username_or_email: str
    password: str
    remember_me: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'username_or_email': self.username_or_email,
            'password': self.password,
            'remember_me': self.remember_me,
        }


@dataclass
class LoginResponseDTO:
    """
    DTO برای پاسخ ورود
    """
    success: bool
    message: str
    user_data: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'user_data': self.user_data,
            'redirect_url': self.redirect_url,
        }


@dataclass
class SignupDTO:
    """
    DTO برای درخواست ثبت نام
    """
    username: str
    email: str
    password: str
    confirm_password: str
    first_name: str = ""
    last_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'confirm_password': self.confirm_password,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }


@dataclass
class SignupResponseDTO:
    """
    DTO برای پاسخ ثبت نام
    """
    success: bool
    message: str
    user_id: Optional[int] = None
    verification_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'user_id': self.user_id,
            'verification_required': self.verification_required,
        }


@dataclass
class EmailVerificationDTO:
    """
    DTO برای تایید ایمیل
    """
    email: str
    verification_code: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'email': self.email,
            'verification_code': self.verification_code,
        }


@dataclass
class EmailVerificationResponseDTO:
    """
    DTO برای پاسخ تایید ایمیل
    """
    success: bool
    message: str
    user_activated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'user_activated': self.user_activated,
        }


@dataclass
class ProfileDTO:
    """
    DTO برای پروفایل کاربر
    """
    phone: str = ""
    address: str = ""
    city: str = ""
    profile_image = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'profile_image': self.profile_image,
        }


@dataclass
class ProfileResponseDTO:
    """
    DTO برای پاسخ پروفایل
    """
    success: bool
    message: str
    profile_data: Optional[Dict[str, Any]] = None
    is_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'profile_data': self.profile_data,
            'is_complete': self.is_complete,
        }


@dataclass
class OAuthDTO:
    """
    DTO برای OAuth authentication
    """
    provider: str
    access_token: str
    user_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'access_token': self.access_token,
            'user_info': self.user_info,
        }


@dataclass
class OAuthResponseDTO:
    """
    DTO برای پاسخ OAuth
    """
    success: bool
    message: str
    user_data: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None
    profile_completion_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'user_data': self.user_data,
            'redirect_url': self.redirect_url,
            'profile_completion_required': self.profile_completion_required,
        }


@dataclass
class PasswordResetDTO:
    """
    DTO برای بازنشانی رمز عبور
    """
    email: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'email': self.email,
        }


@dataclass
class PasswordResetResponseDTO:
    """
    DTO برای پاسخ بازنشانی رمز عبور
    """
    success: bool
    message: str
    reset_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'reset_token': self.reset_token,
        }


@dataclass
class PasswordResetConfirmDTO:
    """
    DTO برای تایید بازنشانی رمز عبور
    """
    token: str
    new_password: str
    confirm_password: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'token': self.token,
            'new_password': self.new_password,
            'confirm_password': self.confirm_password,
        }


@dataclass
class PasswordResetConfirmResponseDTO:
    """
    DTO برای پاسخ تایید بازنشانی رمز عبور
    """
    success: bool
    message: str
    login_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'message': self.message,
            'login_required': self.login_required,
        }


@dataclass
class UserInfoDTO:
    """
    DTO برای اطلاعات کاربر
    """
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    is_active: bool
    date_joined: datetime
    last_login: Optional[datetime]
    profile_complete: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_staff': self.is_staff,
            'is_active': self.is_active,
            'date_joined': self.date_joined.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'profile_complete': self.profile_complete,
        }


@dataclass
class AuthStatsDTO:
    """
    DTO برای آمار احراز هویت
    """
    total_users: int
    active_users: int
    new_users_today: int
    login_attempts_today: int
    failed_logins_today: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_users': self.total_users,
            'active_users': self.active_users,
            'new_users_today': self.new_users_today,
            'login_attempts_today': self.login_attempts_today,
            'failed_logins_today': self.failed_logins_today,
        }