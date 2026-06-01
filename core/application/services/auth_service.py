"""
Authentication Service
سرویس منطق تجاری احراز هویت
"""
import logging
from typing import Optional, Dict, Any
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

from core.domain.entities.auth_entity import AuthEntity, SignupEntity, ProfileEntity, OAuthEntity, PasswordResetEntity
from core.domain.validators.auth_validators import (
    validate_username, validate_email, validate_password, validate_name,
    validate_phone, validate_login_attempt, validate_verification_code,
    validate_oauth_data, validate_profile_completion
)
from core.infrastructure.repositories.auth_repository import AuthRepository
from core.infrastructure.models import TempUser

logger = logging.getLogger(__name__)


class AuthService:
    """
    سرویس منطق تجاری احراز هویت
    """

    def login(self, *, request, username_or_email: str, password: str, ip: str) -> Dict[str, Any]:
        """
        ورود کاربر

        Args:
            request: درخواست HTTP
            username_or_email: نام کاربری یا ایمیل
            password: رمز عبور
            ip: آدرس IP

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # اعتبارسنجی تلاش ورود
            validate_login_attempt(ip)

            # ایجاد entity
            auth_entity = AuthEntity(
                username_or_email=username_or_email,
                password=password,
                ip_address=ip
            )

            # اعتبارسنجی اولیه
            if not auth_entity.validate_credentials():
                raise ValidationError("Invalid login credentials.")

            # یافتن کاربر
            user = AuthRepository.get_user_by_username_or_email(username_or_email)
            if not user:
                raise ValidationError("Invalid username/email or password.")

            # بررسی ban
            if auth_entity.is_banned():
                raise ValidationError("Your account is banned.")

            # احراز هویت
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if not authenticated_user:
                # ثبت تلاش ناموفق
                AuthRepository.log_login_attempt(user, ip, False)
                raise ValidationError("Invalid username/email or password.")

            if not authenticated_user.is_active:
                raise ValidationError("🚫 Account disabaled.")

            # ورود موفق
            login(request, authenticated_user, backend='django.contrib.auth.backends.ModelBackend')

            # بروزرسانی اطلاعات ورود
            AuthRepository.update_user_last_login(authenticated_user, ip)

            # ثبت تلاش موفق
            AuthRepository.log_login_attempt(authenticated_user, ip, True)

            logger.info(f"User {authenticated_user.username} logged in from IP {ip}")

            return {
                'success': True,
                'message': 'ورود موفق',
                'user_data': auth_entity.get_user_info(),
                'redirect_url': '/',
            }

        except ValidationError as e:
            logger.warning(f"Login failed for {username_or_email} from IP {ip}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Login error for {username_or_email}: {str(e)}")
            raise ValidationError("System error. Please try again.")

    def logout(self, request) -> Dict[str, Any]:
        """
        خروج کاربر

        Args:
            request: درخواست HTTP

        Returns:
            Dict[str, Any]: نتیجه عملیات
        """
        try:
            if request.user.is_authenticated:
                logger.info(f"User {request.user.username} logged out")
                logout(request)
                request.session.flush()

            return {
                'success': True,
                'message': 'Logout successful',
                'redirect_url': '/',
            }

        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise ValidationError("System error during logout.")

    def signup(self, *, signup_data: Dict[str, Any], ip: str) -> Dict[str, Any]:
        """
        ثبت نام کاربر جدید

        Args:
            signup_data: داده‌های ثبت نام
            ip: آدرس IP

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # ایجاد entity
            signup_entity = SignupEntity(**signup_data)

            # اعتبارسنجی داده‌ها
            if not signup_entity.validate_basic_info():
                raise ValidationError("Invalid signup data.")

            # اعتبارسنجی فیلدها
            validate_username(signup_entity.username)
            validate_email(signup_entity.email)
            validate_password(signup_entity.password)

            if signup_entity.first_name:
                validate_name(signup_entity.first_name)
            if signup_entity.last_name:
                validate_name(signup_entity.last_name)

            # تولید کد تایید
            verification_code = self._generate_verification_code()

            # ایجاد کاربر موقت
            temp_user_data = signup_entity.get_user_data()
            temp_user_data['verification_code'] = verification_code
            temp_user_data['ip_address'] = ip

            temp_user = AuthRepository.create_temp_user(temp_user_data)

            # ارسال ایمیل تایید
            self._send_verification_email(signup_entity.email, verification_code)

            logger.info(f"User signup initiated for {signup_entity.email}")

            return {
                'success': True,
                'message': 'Signup successful. Please check your email.',
                'verification_required': True,
                'temp_user_id': temp_user.id,
            }

        except ValidationError as e:
            logger.warning(f"Signup failed for {signup_data.get('email', 'unknown')}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            raise ValidationError("System error. Please try again.")

    def verify_email(self, *, email: str, verification_code: str) -> Dict[str, Any]:
        """
        تایید ایمیل و فعالسازی حساب

        Args:
            email: آدرس ایمیل
            verification_code: کد تایید

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # یافتن کاربر موقت
            temp_user = AuthRepository.get_temp_user_by_email(email)
            if not temp_user:
                raise ValidationError("User not found or verification code expired.")

            # اعتبارسنجی کد
            if not validate_verification_code(verification_code, temp_user.verification_code):
                raise ValidationError("Invalid verification code.")

            # ایجاد کاربر واقعی
            user_data = {
                'username': temp_user.username,
                'email': temp_user.email,
                'password': temp_user.password,
                'first_name': temp_user.first_name,
                'last_name': temp_user.last_name,
            }

            user = AuthRepository.create_user(user_data)

            # فعالسازی کاربر
            AuthRepository.activate_user(user)

            # حذف کاربر موقت
            AuthRepository.delete_temp_user(temp_user)

            logger.info(f"Email verified and account activated for {email}")

            return {
                'success': True,
                'message': 'Your account is active. You can now log in.',
                'user_activated': True,
                'user_id': user.id,
            }

        except ValidationError as e:
            logger.warning(f"Email verification failed for {email}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Email verification error for {email}: {str(e)}")
            raise ValidationError("System error. Please try again.")

    def complete_profile(self, *, user: User, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تکمیل پروفایل کاربر

        Args:
            user: کاربر
            profile_data: داده‌های پروفایل

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # ایجاد entity
            profile_entity = ProfileEntity(user=user, **profile_data)

            # اعتبارسنجی داده‌ها
            validate_profile_completion(profile_data)

            # ایجاد/بروزرسانی پروفایل
            profile = AuthRepository.create_or_update_profile(user, profile_data)

            logger.info(f"Profile completed for user {user.username}")

            return {
                'success': True,
                'message': 'پروفایل با موفقیت تکمیل شد.',
                'profile_data': profile_entity.get_profile_data(),
                'is_complete': True,
            }

        except ValidationError as e:
            logger.warning(f"Profile completion failed for {user.username}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Profile completion error for {user.username}: {str(e)}")
            raise ValidationError("خطای سیستمی. لطفاً دوباره تلاش کنید.")

    def oauth_login(self, *, request, provider: str, access_token: str, user_info: Dict[str, Any], ip: str) -> Dict[str, Any]:
        """
        ورود از طریق OAuth

        Args:
            request: درخواست HTTP
            provider: ارائه دهنده OAuth
            access_token: توکن دسترسی
            user_info: اطلاعات کاربر
            ip: آدرس IP

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # اعتبارسنجی داده‌های OAuth
            oauth_data = validate_oauth_data(provider, access_token, user_info)

            # ایجاد entity
            oauth_entity = OAuthEntity(**oauth_data)

            # بررسی وجود کاربر
            user = AuthRepository.get_oauth_user(oauth_entity.email, provider)

            if not user:
                # ایجاد کاربر جدید
                user_data = oauth_entity.get_user_data()
                user = AuthRepository.create_oauth_user(user_data)

            # بررسی کامل بودن پروفایل
            profile = AuthRepository.get_user_profile(user)
            profile_complete = profile and profile.is_profile_complete() if profile else False

            # ورود کاربر
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            AuthRepository.update_user_last_login(user, ip)

            logger.info(f"OAuth login successful for {user.email} via {provider}")

            return {
                'success': True,
                'message': 'ورود موفق از طریق OAuth',
                'user_data': AuthEntity(user=user).get_user_info(),
                'profile_completion_required': not profile_complete,
                'redirect_url': '/complete_profile/' if not profile_complete else '/',
            }

        except ValidationError as e:
            logger.warning(f"OAuth login failed for {provider}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"OAuth login error for {provider}: {str(e)}")
            raise ValidationError("خطای سیستمی در ورود OAuth.")

    def initiate_password_reset(self, *, email: str) -> Dict[str, Any]:
        """
        شروع فرآیند بازنشانی رمز عبور

        Args:
            email: آدرس ایمیل

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # اعتبارسنجی ایمیل
            validate_email(email)

            # یافتن کاربر
            user = AuthRepository.get_user_by_username_or_email(email)
            if not user:
                # برای امنیت، پیام یکسانی بدهیم
                return {
                    'success': True,
                    'message': 'اگر ایمیلی با این آدرس وجود داشته باشد، لینک بازنشانی ارسال خواهد شد.',
                }

            # تولید توکن بازنشانی (در اینجا از کد تایید استفاده می‌کنیم)
            reset_token = self._generate_verification_code()

            # ذخیره توکن در کاربر موقت یا فیلد جداگانه
            # برای سادگی از TempUser استفاده می‌کنیم
            temp_user_data = {
                'username': f"reset_{user.username}",
                'email': email,
                'password': '',  # خالی
                'verification_code': reset_token,
            }

            temp_user = AuthRepository.create_temp_user(temp_user_data)

            # ارسال ایمیل بازنشانی
            self._send_password_reset_email(email, reset_token)

            logger.info(f"Password reset initiated for {email}")

            return {
                'success': True,
                'message': 'لینک بازنشانی رمز عبور به ایمیل شما ارسال شد.',
                'reset_token': reset_token,  # برای تست
            }

        except ValidationError as e:
            logger.warning(f"Password reset initiation failed for {email}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Password reset initiation error for {email}: {str(e)}")
            raise ValidationError("خطای سیستمی. لطفاً دوباره تلاش کنید.")

    def confirm_password_reset(self, *, token: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        """
        تایید بازنشانی رمز عبور

        Args:
            token: توکن بازنشانی
            new_password: رمز عبور جدید
            confirm_password: تایید رمز عبور

        Returns:
            Dict[str, Any]: نتیجه عملیات

        Raises:
            ValidationError: در صورت خطا
        """
        try:
            # یافتن کاربر موقت با توکن
            temp_user = TempUser.objects.filter(verification_code=token).first()
            if not temp_user:
                raise ValidationError("توکن بازنشانی نامعتبر یا منقضی شده است.")

            # یافتن کاربر واقعی
            user = AuthRepository.get_user_by_username_or_email(temp_user.email)
            if not user:
                raise ValidationError("کاربر یافت نشد.")

            # ایجاد entity
            reset_entity = PasswordResetEntity(
                email=temp_user.email,
                reset_token=token,
                new_password=new_password,
                confirm_password=confirm_password
            )

            # اعتبارسنجی رمز عبور جدید
            if not reset_entity.validate_new_password():
                raise ValidationError("رمز عبور جدید نامعتبر است.")

            # اعتبارسنجی رمز عبور
            validate_password(new_password)

            # تغییر رمز عبور
            user.set_password(new_password)
            user.save()

            # حذف کاربر موقت
            AuthRepository.delete_temp_user(temp_user)

            logger.info(f"Password reset successful for {temp_user.email}")

            return {
                'success': True,
                'message': 'رمز عبور با موفقیت تغییر یافت. اکنون می‌توانید وارد شوید.',
                'login_required': True,
            }

        except ValidationError as e:
            logger.warning(f"Password reset confirmation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Password reset confirmation error: {str(e)}")
            raise ValidationError("خطای سیستمی. لطفاً دوباره تلاش کنید.")

    def get_auth_statistics(self) -> Dict[str, Any]:
        """
        دریافت آمار احراز هویت

        Returns:
            Dict[str, Any]: آمار
        """
        try:
            return AuthRepository.get_auth_statistics()
        except Exception as e:
            logger.error(f"Error getting auth statistics: {str(e)}")
            return {}

    def _generate_verification_code(self, length: int = 6) -> str:
        """
        تولید کد تایید

        Args:
            length: طول کد

        Returns:
            str: کد تولید شده
        """
        import random
        import string
        return ''.join(random.choices(string.digits, k=length))

    def _send_verification_email(self, email: str, code: str) -> None:
        """
        ارسال ایمیل تایید

        Args:
            email: آدرس ایمیل
            code: کد تایید
        """
        try:
            subject = 'تایید حساب کاربری - FreshBread'
            message = f"""
            سلام!

            برای فعالسازی حساب کاربری خود، لطفاً از کد زیر استفاده کنید:

            کد تایید: {code}

            اگر این درخواست را شما انجام نداده‌اید، این ایمیل را نادیده بگیرید.

            با تشکر
            تیم FreshBread
            """

            from core.infrastructure.email.email_sender import email_sender
            email_sender.send(
                subject=subject,
                message=message,
                to=email,
                html_message=(
                    "Hello!<br>"
                    "To activate your account, please use the verification code below:<br><br>"
                    f"Verification Code: <strong>{code}</strong>"
                ),
                title="Confirm Your Email",
                wrap=True,
            )

            logger.info(f"Verification email sent to {email}")

        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            raise ValidationError("خطا در ارسال ایمیل تایید.")

    def _send_password_reset_email(self, email: str, token: str) -> None:
        """
        ارسال ایمیل بازنشانی رمز عبور

        Args:
            email: آدرس ایمیل
            token: توکن بازنشانی
        """
        try:
            subject = 'بازنشانی رمز عبور - FreshBread'
            reset_url = f"{settings.SITE_URL}/reset-password/confirm/{token}/"
            message = f"""
            سلام!

            برای بازنشانی رمز عبور حساب کاربری خود، لطفاً روی لینک زیر کلیک کنید:

            {reset_url}

            اگر این درخواست را شما انجام نداده‌اید، این ایمیل را نادیده بگیرید.

            با تشکر
            تیم FreshBread
            """

            from core.infrastructure.email.email_sender import email_sender
            email_sender.send(
                subject=subject,
                message=message,
                to=email,
                html_message=(
                    "Hello!<br>"
                    "To reset your password, click the link below:<br><br>"
                    f"<a href=\"{reset_url}\" style=\"color:#C47A3A; text-decoration:underline;\">{reset_url}</a>"
                ),
                title="Reset Password",
                cta_text="Reset Password",
                action_url=reset_url,
                wrap=True,
            )

            logger.info(f"Password reset email sent to {email}")

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            raise ValidationError("Failed to send password reset email.")


# Instance
auth_service = AuthService()


class AuthException(Exception):
    """استثنای احراز هویت"""
    pass


class AuthValidationException(ValidationError):
    """استثنای اعتبارسنجی احراز هویت"""
    pass
