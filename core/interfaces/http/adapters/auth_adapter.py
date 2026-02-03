"""
Authentication Adapter
Adapter برای اتصال views به سرویس احراز هویت
"""
import logging
from typing import Dict, Any
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.exceptions import ValidationError

from core.application.services.auth_service import auth_service, AuthException, AuthValidationException
from core.application.dto.auth_dto import (
    LoginDTO, LoginResponseDTO, SignupDTO, SignupResponseDTO,
    EmailVerificationDTO, EmailVerificationResponseDTO,
    ProfileDTO, ProfileResponseDTO, OAuthDTO, OAuthResponseDTO,
    PasswordResetDTO, PasswordResetResponseDTO,
    PasswordResetConfirmDTO, PasswordResetConfirmResponseDTO
)
from core.infrastructure.repositories.auth_repository import AuthRepository
from core.interfaces.http.utils.ip import get_client_ip

logger = logging.getLogger(__name__)


class AuthAdapter:
    """
    Adapter برای عملیات احراز هویت
    """

    @staticmethod
    def login_view(request: HttpRequest) -> HttpResponse:
        """
        View ورود کاربر

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ
        """
        if request.method == 'POST':
            try:
                # استخراج داده‌ها
                username_or_email = request.POST.get('username_or_email', '').strip()
                password = request.POST.get('password', '')
                remember_me = request.POST.get('remember_me') == 'on'

                # ایجاد DTO
                login_dto = LoginDTO(
                    username_or_email=username_or_email,
                    password=password,
                    remember_me=remember_me
                )

                # دریافت IP
                ip = get_client_ip(request)

                # اجرای سرویس
                result = auth_service.login(
                    request=request,
                    username_or_email=username_or_email,
                    password=password,
                    ip=ip
                )

                # ایجاد response DTO
                response_dto = LoginResponseDTO(**result)

                # تنظیم پیام
                messages.success(request, response_dto.message)

                # تنظیم session
                if remember_me:
                    request.session.set_expiry(60 * 60 * 24 * 30)  # 30 روز

                # ریدایرکت
                redirect_url = response_dto.redirect_url or '/'
                return redirect(redirect_url)

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('login')
            except Exception as e:
                logger.error(f"Login view error: {str(e)}")
                messages.error(request, "خطای سیستمی. لطفاً دوباره تلاش کنید.")
                return redirect('login')

        # GET request
        return render(request, 'freshbread/login.html')

    @staticmethod
    def logout_view(request: HttpRequest) -> HttpResponse:
        """
        View خروج کاربر

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ
        """
        try:
            result = auth_service.logout(request)
            messages.success(request, result['message'])

            redirect_url = result.get('redirect_url', '/')
            return redirect(redirect_url)

        except Exception as e:
            logger.error(f"Logout view error: {str(e)}")
            messages.error(request, "خطای سیستمی در خروج.")
            return redirect('/')

    @staticmethod
    def signup_view(request: HttpRequest) -> HttpResponse:
        """
        View ثبت نام کاربر

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ
        """
        if request.method == 'POST':
            try:
                # استخراج داده‌ها
                signup_data = {
                    'username': request.POST.get('username', '').strip(),
                    'email': request.POST.get('email', '').strip(),
                    'password': request.POST.get('password', ''),
                    'confirm_password': request.POST.get('confirm_password', ''),
                    'first_name': request.POST.get('first_name', '').strip(),
                    'last_name': request.POST.get('last_name', '').strip(),
                }

                # دریافت IP
                ip = get_client_ip(request)

                # اجرای سرویس
                result = auth_service.signup(signup_data=signup_data, ip=ip)

                # ایجاد response DTO
                response_dto = SignupResponseDTO(**result)

                # تنظیم پیام
                messages.success(request, response_dto.message)

                # ریدایرکت به صفحه تایید ایمیل
                return redirect('verify_email')

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('signup')
            except Exception as e:
                logger.error(f"Signup view error: {str(e)}")
                messages.error(request, "خطای سیستمی. لطفاً دوباره تلاش کنید.")
                return redirect('signup')

        # GET request
        return render(request, 'freshbread/signup.html')

    @staticmethod
    def verify_email_view(request: HttpRequest) -> HttpResponse:
        """
        View تایید ایمیل

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ
        """
        if request.method == 'POST':
            try:
                # استخراج داده‌ها
                email = request.POST.get('email', '').strip()
                verification_code = request.POST.get('verification_code', '').strip()

                # ایجاد DTO
                verification_dto = EmailVerificationDTO(
                    email=email,
                    verification_code=verification_code
                )

                # اجرای سرویس
                result = auth_service.verify_email(
                    email=email,
                    verification_code=verification_code
                )

                # ایجاد response DTO
                response_dto = EmailVerificationResponseDTO(**result)

                # تنظیم پیام
                messages.success(request, response_dto.message)

                # ریدایرکت به صفحه ورود
                return redirect('login')

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('verify_email')
            except Exception as e:
                logger.error(f"Email verification view error: {str(e)}")
                messages.error(request, "خطای سیستمی. لطفاً دوباره تلاش کنید.")
                return redirect('verify_email')

        # GET request
        return render(request, 'freshbread/verify_email.html')

    @staticmethod
    def complete_profile_view(request: HttpRequest) -> HttpResponse:
        """
        View تکمیل پروفایل

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ
        """
        if not request.user.is_authenticated:
            return redirect('login')

        if request.method == 'POST':
            try:
                # استخراج داده‌ها
                profile_data = {
                    'phone': request.POST.get('phone', '').strip(),
                    'address': request.POST.get('address', '').strip(),
                    'city': request.POST.get('city', '').strip(),
                    'profile_image': request.FILES.get('profile_image'),
                }

                # اجرای سرویس
                result = auth_service.complete_profile(
                    user=request.user,
                    profile_data=profile_data
                )

                # ایجاد response DTO
                response_dto = ProfileResponseDTO(**result)

                # تنظیم پیام
                messages.success(request, response_dto.message)

                # ریدایرکت به پروفایل
                return redirect('profile')

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('complete_profile')
            except Exception as e:
                logger.error(f"Complete profile view error: {str(e)}")
                messages.error(request, "خطای سیستمی. لطفاً دوباره تلاش کنید.")
                return redirect('complete_profile')

        # GET request - نمایش فرم تکمیل پروفایل
        return render(request, 'freshbread/complete_profile.html')

    @staticmethod
    def oauth_login_view(request: HttpRequest, provider: str) -> HttpResponse:
        """
        View ورود OAuth

        Args:
            request: درخواست HTTP
            provider: ارائه دهنده OAuth

        Returns:
            HttpResponse: پاسخ
        """
        try:
            # در اینجا باید منطق OAuth پیاده‌سازی شود
            # برای سادگی، فرض می‌کنیم داده‌های OAuth از request آمده

            # این قسمت باید با کتابخانه OAuth مناسب پیاده‌سازی شود
            # مانند social-auth-app-django

            # شبیه‌سازی داده‌های OAuth
            oauth_data = {
                'provider': provider,
                'access_token': request.GET.get('access_token', ''),
                'user_info': {
                    'email': request.GET.get('email', ''),
                    'name': request.GET.get('name', ''),
                    'picture': request.GET.get('picture', ''),
                }
            }

            # ایجاد DTO
            oauth_dto = OAuthDTO(**oauth_data)

            # دریافت IP
            ip = get_client_ip(request)

            # اجرای سرویس
            result = auth_service.oauth_login(
                request=request,
                provider=provider,
                access_token=oauth_data['access_token'],
                user_info=oauth_data['user_info'],
                ip=ip
            )

            # ایجاد response DTO
            response_dto = OAuthResponseDTO(**result)

            # تنظیم پیام
            messages.success(request, response_dto.message)

            # ریدایرکت
            redirect_url = response_dto.redirect_url or '/'
            return redirect(redirect_url)

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('login')
        except Exception as e:
            logger.error(f"OAuth login view error for {provider}: {str(e)}")
            messages.error(request, "خطای سیستمی در ورود OAuth.")
            return redirect('login')

    @staticmethod
    def password_reset_view(request: HttpRequest) -> HttpResponse:
        """
        View درخواست بازنشانی رمز عبور

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ
        """
        if request.method == 'POST':
            try:
                # استخراج داده‌ها
                email = request.POST.get('email', '').strip()

                # ایجاد DTO
                reset_dto = PasswordResetDTO(email=email)

                # اجرای سرویس
                result = auth_service.initiate_password_reset(email=email)

                # ایجاد response DTO
                response_dto = PasswordResetResponseDTO(**result)

                # تنظیم پیام
                messages.success(request, response_dto.message)

                # ریدایرکت به صفحه تایید
                return redirect('password_reset_done')

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('password_reset')
            except Exception as e:
                logger.error(f"Password reset view error: {str(e)}")
                messages.error(request, "خطای سیستمی. لطفاً دوباره تلاش کنید.")
                return redirect('password_reset')

        # GET request
        return render(request, 'freshbread/password_reset.html')

    @staticmethod
    def password_reset_confirm_view(request: HttpRequest, token: str) -> HttpResponse:
        """
        View تایید بازنشانی رمز عبور

        Args:
            request: درخواست HTTP
            token: توکن بازنشانی

        Returns:
            HttpResponse: پاسخ
        """
        if request.method == 'POST':
            try:
                # استخراج داده‌ها
                new_password = request.POST.get('new_password', '')
                confirm_password = request.POST.get('confirm_password', '')

                # ایجاد DTO
                confirm_dto = PasswordResetConfirmDTO(
                    token=token,
                    new_password=new_password,
                    confirm_password=confirm_password
                )

                # اجرای سرویس
                result = auth_service.confirm_password_reset(
                    token=token,
                    new_password=new_password,
                    confirm_password=confirm_password
                )

                # ایجاد response DTO
                response_dto = PasswordResetConfirmResponseDTO(**result)

                # تنظیم پیام
                messages.success(request, response_dto.message)

                # ریدایرکت به صفحه ورود
                return redirect('login')

            except ValidationError as e:
                messages.error(request, str(e))
                return redirect('password_reset_confirm', token=token)
            except Exception as e:
                logger.error(f"Password reset confirm view error: {str(e)}")
                messages.error(request, "خطای سیستمی. لطفاً دوباره تلاش کنید.")
                return redirect('password_reset_confirm', token=token)

        # GET request
        return render(request, 'freshbread/password_reset_confirm.html', {'token': token})

    @staticmethod
    def check_profile_view(request: HttpRequest) -> HttpResponse:
        """
        View بررسی وضعیت پروفایل

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ JSON یا ریدایرکت
        """
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            profile = AuthRepository.get_user_profile(request.user)

            if profile and profile.is_profile_complete():
                # پروفایل کامل است
                return redirect('profile')
            else:
                # نیاز به تکمیل پروفایل
                return redirect('complete_profile')

        except Exception as e:
            logger.error(f"Check profile view error: {str(e)}")
            return redirect('profile')

    @staticmethod
    def api_login(request: HttpRequest) -> HttpResponse:
        """
        API endpoint برای ورود

        Args:
            request: درخواست HTTP

        Returns:
            HttpResponse: پاسخ JSON
        """
        from django.http import JsonResponse

        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)

        try:
            # استخراج داده‌ها از JSON
            import json
            data = json.loads(request.body)

            username_or_email = data.get('username_or_email', '').strip()
            password = data.get('password', '')

            # دریافت IP
            ip = get_client_ip(request)

            # اجرای سرویس
            result = auth_service.login(
                request=request,
                username_or_email=username_or_email,
                password=password,
                ip=ip
            )

            return JsonResponse(result)

        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"API login error: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)