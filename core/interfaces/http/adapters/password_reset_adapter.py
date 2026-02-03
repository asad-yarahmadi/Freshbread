"""
Adapter برای تبدیل درخواست‌های HTTP به DTO‌ها
این فایل نشان‌دهنده آن است که چگونه views جدید می‌توانند سرویس را استفاده کنند
"""
from django.http import HttpRequest
from django.utils.text import get_valid_filename
from core.application.dto.password_reset_dto import (
    PasswordResetInitiateDTO,
    PasswordResetVerifyDTO,
    PasswordResetCompleteDTO
)


def get_client_ip(request: HttpRequest) -> str:
    """
    گرفتن IP آدرس کاربر از request
    
    Args:
        request: Django HttpRequest
    
    Returns:
        str: IP آدرس
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def create_reset_initiate_dto(request: HttpRequest, username: str, email: str) -> PasswordResetInitiateDTO:
    """
    ایجاد DTO برای درخواست اولیه‌ٔ ریست از request
    
    Args:
        request: Django HttpRequest
        username: نام کاربری
        email: ایمیل
    
    Returns:
        PasswordResetInitiateDTO
    """
    return PasswordResetInitiateDTO(
        username=username.strip(),
        email=email.strip(),
        ip_address=get_client_ip(request)
    )


def create_reset_verify_dto(request: HttpRequest, username: str, code: str) -> PasswordResetVerifyDTO:
    """
    ایجاد DTO برای تایید کد از request
    
    Args:
        request: Django HttpRequest
        username: نام کاربری (از session)
        code: کد تایید
    
    Returns:
        PasswordResetVerifyDTO
    """
    return PasswordResetVerifyDTO(
        username=username.strip(),
        verification_code=code.strip(),
        ip_address=get_client_ip(request)
    )


def create_reset_complete_dto(
    request: HttpRequest, 
    username: str, 
    password: str, 
    password_confirm: str
) -> PasswordResetCompleteDTO:
    """
    ایجاد DTO برای تکمیل ریست پسورد از request
    
    Args:
        request: Django HttpRequest
        username: نام کاربری (از session)
        password: پسورد جدید
        password_confirm: تأیید پسورد
    
    Returns:
        PasswordResetCompleteDTO
    """
    return PasswordResetCompleteDTO(
        username=username.strip(),
        new_password=password,
        new_password_confirm=password_confirm,
        ip_address=get_client_ip(request)
    )
