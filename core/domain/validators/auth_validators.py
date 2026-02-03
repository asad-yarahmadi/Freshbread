"""
Authentication Validators
توابع اعتبارسنجی برای عملیات احراز هویت
"""
import re
from typing import Optional, Dict, Any
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from core.infrastructure.models import LoginAttempt


def validate_username(value: str) -> str:
    """
    اعتبارسنجی نام کاربری

    Args:
        value: نام کاربری

    Returns:
        str: نام کاربری اعتبارسنجی شده

    Raises:
        ValidationError: در صورت نامعتبر بودن
    """
    if not value:
        raise ValidationError("Username cannot be empty.")

    if len(value) < 3:
        raise ValidationError("Username must be at least 3 characters.")

    if len(value) > 30:
        raise ValidationError("Username cannot exceed 30 characters.")

    # بررسی کاراکترهای مجاز
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise ValidationError("Username may contain letters, numbers, and underscores only.")

    # بررسی یکتا بودن
    if User.objects.filter(username__iexact=value).exists():
        raise ValidationError("This username is already taken.")

    return value


def validate_email(value: str) -> str:
    """
    اعتبارسنجی ایمیل

    Args:
        value: آدرس ایمیل

    Returns:
        str: ایمیل اعتبارسنجی شده

    Raises:
        ValidationError: در صورت نامعتبر بودن
    """
    if not value:
        raise ValidationError("Email cannot be empty.")

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValidationError("Invalid email format.")

    # بررسی یکتا بودن
    if User.objects.filter(email__iexact=value).exists():
        raise ValidationError("This email is already registered.")

    return value.lower()


def validate_password(value: str) -> str:
    """
    اعتبارسنجی رمز عبور

    Args:
        value: رمز عبور

    Returns:
        str: رمز عبور اعتبارسنجی شده

    Raises:
        ValidationError: در صورت نامعتبر بودن
    """
    if not value:
        raise ValidationError("Password cannot be empty.")

    if len(value) < 6:
        raise ValidationError("Password must be at least 6 characters.")

    if len(value) > 128:
        raise ValidationError("Password cannot exceed 128 characters.")

    # بررسی وجود حداقل یک حرف و یک عدد
    if not re.search(r'[a-zA-Z]', value):
        raise ValidationError("Password must contain at least one letter.")

    if not re.search(r'[0-9]', value):
        raise ValidationError("Password must contain at least one number.")

    return value


def validate_name(value: str) -> str:
    """
    اعتبارسنجی نام و نام خانوادگی

    Args:
        value: نام

    Returns:
        str: نام اعتبارسنجی شده

    Raises:
        ValidationError: در صورت نامعتبر بودن
    """
    if not value:
        raise ValidationError("This field cannot be empty.")

    if len(value.strip()) < 2:
        raise ValidationError("Name must be at least 2 characters.")

    if len(value) > 50:
        raise ValidationError("Name cannot exceed 50 characters.")

    # بررسی کاراکترهای مجاز (فارسی و انگلیسی)
    if not re.match(r'^[a-zA-Zآ-ی\s]+$', value):
        raise ValidationError("Name may contain letters only.")

    return value.strip()


def validate_phone(value: str) -> str:
    """
    اعتبارسنجی شماره تلفن

    Args:
        value: شماره تلفن

    Returns:
        str: شماره تلفن اعتبارسنجی شده

    Raises:
        ValidationError: در صورت نامعتبر بودن
    """
    if not value:
        raise ValidationError("Phone number cannot be empty.")

    # پاک کردن کاراکترهای غیر عددی
    clean_phone = re.sub(r'[^\d]', '', value)

    if len(clean_phone) < 10:
        raise ValidationError("Phone number must be at least 10 digits.")

    if len(clean_phone) > 15:
        raise ValidationError("Phone number cannot exceed 15 digits.")

    # بررسی فرمت ایرانی
    if not clean_phone.startswith(('09', '9')):
        raise ValidationError("Phone number must start with 09.")

    return clean_phone


def validate_login_attempt(ip_address: str, user: Optional[User] = None) -> None:
    """
    اعتبارسنجی تلاش برای ورود

    Args:
        ip_address: آدرس IP
        user: کاربر (اختیاری)

    Raises:
        ValidationError: در صورت محدودیت
    """
    now = timezone.now()

    # بررسی محدودیت IP
    threshold = now - timedelta(minutes=30)
    recent_attempts = LoginAttempt.objects.filter(
        ip_address=ip_address,
        timestamp__gte=threshold
    ).count()

    if recent_attempts >= 10:
        raise ValidationError("Too many login attempts from this IP. Please wait 30 minutes.")

    # بررسی محدودیت کاربر
    if user:
        user_attempts = LoginAttempt.objects.filter(
            user=user,
            timestamp__gte=threshold
        ).count()

        if user_attempts >= 5:
            raise ValidationError("Too many login attempts for this account. Please wait 30 minutes.")

    # بررسی ban
    ip_ban = LoginAttempt.objects.filter(
        ip_address=ip_address,
        blocked_until__gt=now
    ).exists()

    if ip_ban:
        raise ValidationError("This IP is banned.")

    if user:
        user_ban = LoginAttempt.objects.filter(
            user=user,
            blocked_until__gt=now
        ).exists()

        if user_ban:
            raise ValidationError("This account is banned.")


def validate_verification_code(code: str, expected_code: str) -> bool:
    """
    اعتبارسنجی کد تایید

    Args:
        code: کد وارد شده
        expected_code: کد مورد انتظار

    Returns:
        bool: معتبر بودن کد
    """
    if not code or not expected_code:
        return False

    return code.strip() == expected_code.strip()


def validate_oauth_data(provider: str, access_token: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    اعتبارسنجی داده‌های OAuth

    Args:
        provider: ارائه دهنده OAuth
        access_token: توکن دسترسی
        user_info: اطلاعات کاربر

    Returns:
        Dict[str, Any]: داده‌های اعتبارسنجی شده

    Raises:
        ValidationError: در صورت نامعتبر بودن
    """
    if not provider or provider not in ['google', 'facebook', 'twitter']:
        raise ValidationError("Invalid OAuth provider.")

    if not access_token:
        raise ValidationError("OAuth access token not found.")

    if not user_info or 'email' not in user_info:
        raise ValidationError("OAuth user information is incomplete.")

    email = user_info.get('email', '').lower()
    if not validate_email(email):
        raise ValidationError("ایمیل OAuth نامعتبر است.")

    return {
        'provider': provider,
        'access_token': access_token,
        'email': email,
        'name': user_info.get('name', ''),
        'picture': user_info.get('picture', ''),
        'user_info': user_info,
    }


def validate_profile_completion(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    اعتبارسنجی کامل بودن پروفایل

    Args:
        profile_data: داده‌های پروفایل

    Returns:
        Dict[str, Any]: داده‌های اعتبارسنجی شده

    Raises:
        ValidationError: در صورت ناقص بودن
    """
    required_fields = ['phone', 'address', 'city']

    for field in required_fields:
        if not profile_data.get(field, '').strip():
            raise ValidationError(f"فیلد {field} اجباری است.")

    # اعتبارسنجی شماره تلفن
    phone = validate_phone(profile_data['phone'])
    profile_data['phone'] = phone

    # اعتبارسنجی آدرس
    address = profile_data['address'].strip()
    if len(address) < 10:
        raise ValidationError("آدرس باید حداقل ۱۰ کاراکتر باشد.")
    if len(address) > 500:
        raise ValidationError("آدرس نمی‌تواند بیش از ۵۰۰ کاراکتر باشد.")

    # اعتبارسنجی شهر
    city = profile_data['city'].strip()
    if len(city) < 2:
        raise ValidationError("نام شهر باید حداقل ۲ کاراکتر باشد.")
    if len(city) > 100:
        raise ValidationError("نام شهر نمی‌تواند بیش از ۱۰۰ کاراکتر باشد.")

    return profile_data