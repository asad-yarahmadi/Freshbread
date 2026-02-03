"""
Data Transfer Objects (DTOs) برای Password Reset
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PasswordResetInitiateDTO:
    """
    DTO برای درخواست اولیهٔ ریست پسورد
    """
    username: str
    email: str
    ip_address: str


@dataclass
class PasswordResetVerifyDTO:
    """
    DTO برای تایید کد
    """
    username: str
    verification_code: str
    ip_address: str


@dataclass
class PasswordResetCompleteDTO:
    """
    DTO برای تکمیل ریست پسورد
    """
    username: str
    new_password: str
    new_password_confirm: str
    ip_address: str
