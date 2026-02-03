"""
Application Layer: Password Reset Service
منطق تجاری برای فرآیند ریست پسورد (3 مرحله‌ای)
"""
from datetime import timedelta
from typing import Tuple

from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from ...domain.utils.verification_code import generate_verification_code
from ...infrastructure.repositories.user_repository import UserRepository


class PasswordResetException(Exception):
    """Exception اختصاصی برای خطاهای ریست پسورد"""
    pass


class RateLimitedException(PasswordResetException):
    """Exception برای تجاوز محدودیت تعداد تلاش‌ها"""
    pass


class PasswordResetService:
    """
    سرویس مدیریت فرآیند ریست پسورد
    شامل 3 مرحله: درخواست، تایید کد، تعیین پسورد جدید
    """
    
    # ثابت‌های محدودیت
    MAX_FAILURES_PER_IP = 3
    FAILURE_BAN_DURATION = 60 * 60 * 30  # 30 ساعت
    CODE_EXPIRY_SECONDS = 300  # 5 دقیقه (نه 2 دقیقه)
    MAX_RESETS_PER_30_HOURS = 2
    STEP_COMPLETION_TIMEOUT = 600  # 10 دقیقه
    
    @classmethod
    def initiate_reset(cls, username: str, email: str, ip: str) -> str:
        """
        مرحله 1: درخواست ریست پسورد
        کاربر username و email خود را وارد می‌کند
        سرویس کد تایید را ایمیل می‌کند
        
        Args:
            username: نام کاربری
            email: ایمیل
            ip: IP آدرس کاربر
        
        Returns:
            str: نام کاربری برای session
        
        Raises:
            RateLimitedException: اگر تعداد تلاش‌ها بیشتر از حد است
            PasswordResetException: اگر کاربر پیدا نشد
        """
        # بررسی محدودیت تلاش‌ها
        failure_key = f"reset_failures_{ip}"
        failures = cache.get(failure_key, 0)
        
        if failures >= cls.MAX_FAILURES_PER_IP:
            ban_key = f"ban_{ip}"
            cache.set(ban_key, True, cls.FAILURE_BAN_DURATION)
            raise RateLimitedException(
                "⛔ شما برای 30 ساعت محدود شده‌اید."
            )
        
        # گرفتن کاربر
        user = UserRepository.get_user_by_username_and_email(username, email)
        if not user:
            failures += 1
            cache.set(failure_key, failures, cls.FAILURE_BAN_DURATION)
            raise PasswordResetException(
                "❌ نام کاربری و ایمیل تطابق ندارند."
            )
        
        # تولید کد و ذخیره در cache
        code = generate_verification_code()
        code_cache_key = f"reset_code_{user.username}"
        cache.set(code_cache_key, code, cls.CODE_EXPIRY_SECONDS)
        
        # ارسال ایمیل
        cls._send_verification_email(username, user.email, code)
        
        return user.username
    
    @classmethod
    def verify_code(cls, username: str, code: str, ip: str) -> bool:
        """
        مرحله 2: تایید کد تایید
        کاربر کد دریافت شده را وارد می‌کند
        
        Args:
            username: نام کاربری
            code: کد تایید وارد شده
            ip: IP آدرس کاربر
        
        Returns:
            bool: True اگر کد درست باشد
        
        Raises:
            RateLimitedException: اگر تعداد تلاش‌های اشتباه بیشتر از حد است
            PasswordResetException: اگر کد اشتباه یا منقضی باشد
        """
        failure_key = f"reset_failures_{ip}"
        failures = cache.get(failure_key, 0)
        
        code_cache_key = f"reset_code_{username}"
        saved_code = cache.get(code_cache_key)
        
        if not saved_code or code != saved_code:
            failures += 1
            cache.set(failure_key, failures, cls.FAILURE_BAN_DURATION)
            
            if failures >= cls.MAX_FAILURES_PER_IP:
                ban_key = f"ban_{ip}"
                cache.set(ban_key, True, cls.FAILURE_BAN_DURATION)
                raise RateLimitedException(
                    "⛔ شما برای 30 ساعت محدود شده‌اید."
                )
            
            raise PasswordResetException(
                "❌ کد تایید اشتباه است."
            )
        
        # علامت‌گذاری مرحله 2 به عنوان تکمیل شده
        step_completion_key = f"step1_completed_{ip}"
        cache.set(step_completion_key, True, cls.STEP_COMPLETION_TIMEOUT)
        
        return True
    
    @classmethod
    def reset_password(cls, username: str, new_password: str, ip: str) -> bool:
        """
        مرحله 3: تعیین پسورد جدید
        کاربر پسورد جدید خود را وارد می‌کند
        
        Args:
            username: نام کاربری
            new_password: پسورد جدید (plain text)
            ip: IP آدرس کاربر
        
        Returns:
            bool: True اگر موفق باشد
        
        Raises:
            RateLimitedException: اگر تعداد ریست‌های مجاز تجاوز شود
            ValidationError: اگر پسورد معتبر نباشد
            PasswordResetException: اگر کاربر پیدا نشود
        """
        # اعتبارسنجی پسورد
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        # گرفتن کاربر
        user = UserRepository.get_user_by_username(username)
        if not user:
            raise PasswordResetException(
                "❌ کاربر پیدا نشد."
            )
        
        # بررسی محدودیت ریست (2 بار در 30 ساعت)
        reset_times_key = f"reset_times_{username}"
        reset_times = cache.get(reset_times_key, [])
        now = timezone.now()
        
        # فیلتر کردن ریست‌های قدیمی‌تر از 30 ساعت
        reset_times = [
            t for t in reset_times 
            if now - t < timedelta(hours=30)
        ]
        
        if len(reset_times) >= cls.MAX_RESETS_PER_30_HOURS:
            raise RateLimitedException(
                "⛔ شما فقط می‌توانید در 30 ساعت 2 بار پسورد خود را تغییر دهید."
            )
        
        # بروزرسانی پسورد
        UserRepository.update_password(user, new_password)
        
        # ثبت زمان ریست
        reset_times.append(now)
        cache.set(reset_times_key, reset_times, 60 * 60 * 30)
        
        # ارسال ایمیل تأیید
        cls._send_password_changed_email(username, user.email)
        
        return True
    
    @staticmethod
    def _send_verification_email(username: str, email: str, code: str) -> None:
        """
        ارسال ایمیل حاوی کد تایید
        
        Args:
            username: نام کاربری
            email: آدرس ایمیل
            code: کد تایید
        """
        try:
            send_mail(
                subject="Password Reset Verification Code - Fresh Bread Bakery",
                message=(
                    f"Hello {username},\n\n"
                    f"🔸 Verification Code: {code}\n\n"
                    "This code will expire in 5 minutes.\n\n"
                    "Fresh Bread Bakery Team\nhttp://127.0.0.1:8000"
                ),
                from_email="order.freshbread911@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            raise PasswordResetException(
                f"❌ خطا در ارسال ایمیل: {str(e)}"
            )
    
    @staticmethod
    def _send_password_changed_email(username: str, email: str) -> None:
        """
        ارسال ایمیل تأیید تغییر پسورد
        
        Args:
            username: نام کاربری
            email: آدرس ایمیل
        """
        try:
            send_mail(
                subject="Password changed - Fresh Bread Bakery",
                message=(
                    f"Hello {username},\n\n"
                    "Your account password has been changed.\n\n"
                    "If you did not do this, please contact us.\n\n"
                    "Fresh Bread Bakery Team\nhttp://127.0.0.1:8000"
                ),
                from_email="order.freshbread911@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            # اگر ایمیل ارسال نشد، نباید مانع موفقیت ریست شود
            pass
    
    @staticmethod
    def check_ip_ban(ip: str) -> bool:
        """
        بررسی اینکه IP محدود شده‌ است یا نه
        
        Args:
            ip: IP آدرس
        
        Returns:
            bool: True اگر IP محدود باشد
        """
        ban_key = f"ban_{ip}"
        return cache.get(ban_key, False)
    
    @staticmethod
    def check_step_completion(ip: str) -> bool:
        """
        بررسی تکمیل مرحله 2 (تایید کد)
        
        Args:
            ip: IP آدرس
        
        Returns:
            bool: True اگر مرحله 2 تکمیل شده‌ باشد
        """
        step_key = f"step1_completed_{ip}"
        return cache.get(step_key, False)
