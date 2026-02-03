from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

def admin_login_protect(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        from .utils.ip import get_client_ip
        ip = get_client_ip(request)
        now = timezone.now()
        from core.infrastructure.models import LoginAttempt
        filter_q = Q(ip_address=ip)
        if getattr(user, 'is_authenticated', False):
            filter_q = filter_q | Q(user=user)
        attempts = LoginAttempt.objects.filter(filter_q).order_by('-timestamp')[:5]
        blocked = any(a.is_blocked() for a in attempts)
        if blocked or not (user.is_authenticated and (user.is_staff or user.is_superuser)):
            messages.error(request, "❌ You are not allowed to access this page or are temporarily blocked.")
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def email_verified_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('su')
        profile = getattr(request.user, 'profile', None)
        is_verified = getattr(profile, 'is_verified', True)
        if not is_verified:
            messages.warning(request, "⚠️ You must verify your email to access this page.")
            return redirect('verify_email')
        return view_func(request, *args, **kwargs)
    return wrapper

def check_temp_user(func):
    def wrapper(request, *args, **kwargs):
        from core.infrastructure.models import TempUser
        email = request.GET.get('email') or request.POST.get('email')
        username = request.GET.get('username') or request.POST.get('username')
        temp_user = None
        if email:
            temp_user = TempUser.objects.filter(email=email).first()
        elif username:
            temp_user = TempUser.objects.filter(username=username).first()
        if not temp_user:
            messages.error(request, "❌ Information not found.")
            return redirect('su')
        if getattr(temp_user, 'is_verified', False):
            messages.warning(request, "⚠️ Your email was verified.")
            return redirect('ru')
        return func(request, *args, **kwargs)
    return wrapper

def verify_rate_limit(key_prefix, rate=5, period=60):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            ip = request.META.get("REMOTE_ADDR")
            cache_key = f"{key_prefix}:{ip}"
            attempts = cache.get(cache_key, 0)
            if attempts >= rate:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("⛔ A lot of requests. wait for a Second")
            cache.set(cache_key, attempts + 1, period)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def anonymous_or_incomplete_required(redirect_url='/'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                profile = getattr(user, 'profile', None)
                if profile and getattr(profile, 'profile_completed', False) and getattr(profile, 'acc_prpo', False):
                    return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def profile_completed_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must login first ⚠️")
            return redirect("ru")
        profile = getattr(request.user, "socialprofile", None)
        if profile and not getattr(profile, 'profile_completed', True):
            messages.error(request, "Please complete your profile 🙏")
            return redirect("complete_social_profile_view")
        return view_func(request, *args, **kwargs)
    return wrapper

def cart_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        import time
        block_until = request.session.get('checkout_block_until')
        if block_until and time.time() < float(block_until):
            from django.contrib import messages
            messages.error(request, "Checkout is temporarily blocked. Please wait and try again.")
            from django.shortcuts import redirect
            return redirect('reservation')
        try:
            from core.application.services.cart_service import CartService
            summary = CartService.get_cart_summary(request)
            total_items = summary.get('total_items', 0)
            if not total_items:
                from django.contrib import messages
                messages.warning(request, "Your cart is empty. Please add items before checkout.")
                from django.shortcuts import redirect
                return redirect('reservation')
        except Exception:
            from django.shortcuts import redirect
            return redirect('reservation')
        return view_func(request, *args, **kwargs)
    return _wrapped

def checkout_step1_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        temp = request.session.get('temp_checkout') or {}
        if not temp.get('temp_user_id') or not temp.get('step1_ok'):
            from django.contrib import messages
            messages.error(request, "Please complete step 1.")
            from django.shortcuts import redirect
            return redirect('checkout_s1')
        return view_func(request, *args, **kwargs)
    return _wrapped

def checkout_step2_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        temp = request.session.get('temp_checkout') or {}
        if not temp.get('temp_user_id') or not temp.get('step2_ok'):
            from django.contrib import messages
            messages.error(request, "Please complete step 2.")
            from django.shortcuts import redirect
            return redirect('checkout_s2')
        return view_func(request, *args, **kwargs)
    return _wrapped