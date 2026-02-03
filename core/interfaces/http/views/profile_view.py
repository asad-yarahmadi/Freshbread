from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import re
import requests

def complete_profile_view(request):
    # Lazy imports
    from core.application.services.profile_service import profile_service
    from core.application.security.ddos_checker import ddos_checker

    blocked = ddos_checker.check(request)
    if blocked:
        return blocked

    if request.method == "POST":
        try:
            profile_service.complete_profile_after_signup(
                request=request,
                first_name=request.POST.get("first_name", ""),
                last_name=request.POST.get("last_name", "")
            )
            return redirect("index")
        except Exception as e:
            messages.error(request, str(e))

    return render(request, "freshbread/profile/complete_profile.html")

@login_required
@login_required
def profile(request):
    from core.application.services.order_service import OrderService
    from core.infrastructure.models import Profile
    import random, string

    orders = OrderService.get_user_orders(request.user)

    # فرض می‌کنیم orders لیست dict است → از کلید استفاده کن
    active_orders = [
        o for o in orders
        if o.get('status') in {'pending', 'processing', 'cooking', 'queued', 'sending', 'ready'}
    ]

    delivered_orders = [o for o in orders if o.get('status') == 'delivered']
    cancelled_orders   = [o for o in orders if o.get('status') == 'cancelled']

    profile = getattr(request.user, 'profile', None)
    if not profile:
        profile = Profile.objects.create(user=request.user)
    if not profile.referral_code:
        rc = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        while Profile.objects.filter(referral_code=rc).exists():
            rc = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        profile.referral_code = rc
        profile.save(update_fields=["referral_code"])

    context = {
        "orders": orders,               # اگر هنوز لازم داری
        "active_orders": active_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders,
        "profile": profile,
    }

    return render(request, "freshbread/profile/pf.html", context)
@login_required
def edit_profile(request):
    from core.infrastructure.models import Profile
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile:
        profile = Profile.objects.create(user=user)

    # preload values for template binding
    values = {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "email": user.email or "",
        "phone": getattr(profile, "phone", "") or "",
        "postal_code": getattr(profile, "postal_code", "") or "",
        "bio": getattr(profile, "bio", "") or "hi there! im using Freshbread.",
        "latitude": "",
        "longitude": "",
    }

    if request.method == "POST":
        # rate limit: max 2 edits per 30 hours
        key = f"profile_edit:{user.id}"
        data = cache.get(key)
        if data is None:
            cache.set(key, {"count": 1}, timeout=30 * 60 * 60)
        else:
            if data.get("count", 0) >= 2:
                messages.error(request, "You have reached the limit of 2 edits in 30 hours.")
                return redirect("profile")
            data["count"] = data.get("count", 0) + 1
            cache.set(key, data, timeout=30 * 60 * 60)

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        bio = request.POST.get("bio", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        values.update({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "postal_code": postal_code,
            "bio": bio or "hi there! im using Freshbread.",
            "latitude": latitude or "",
            "longitude": longitude or "",
        })

        try:
            avatar_file = request.FILES.get("avatar")
            avatar_dataurl = request.POST.get("avatar_cropped")
            if avatar_dataurl:
                if not avatar_dataurl.startswith("data:image/"):
                    raise ValidationError("Invalid image data.")
                import base64
                from django.core.files.base import ContentFile
                header, b64 = avatar_dataurl.split(",", 1)
                data = base64.b64decode(b64)
                if len(data) > 2 * 1024 * 1024:
                    raise ValidationError("Image must be less than 2MB.")
                profile.avatar.save("avatar_cropped.png", ContentFile(data), save=False)
            if avatar_file:
                if not (avatar_file.content_type or "").startswith("image/"):
                    raise ValidationError("Invalid image file.")
                if avatar_file.size > 2 * 1024 * 1024:
                    raise ValidationError("Image must be less than 2MB.")
                profile.avatar = avatar_file
            # email update and verification gate
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if email and email != (user.email or ""):
                if not re.match(email_pattern, email):
                    raise ValidationError("Invalid email format.")
                from django.contrib.auth.models import User
                exists = User.objects.filter(email__iexact=email).exclude(id=user.id).exists()
                if exists:
                    raise ValidationError("This email is already registered.")
                # create temp user and send verification
                from core.infrastructure.models import TempUser
                from core.domain.utils.verification import generate_verification_code
                from django.utils import timezone
                from datetime import timedelta
                from core.infrastructure.email.email_sender import email_sender
                code = generate_verification_code()
                now = timezone.now()
                temp, _ = TempUser.objects.get_or_create(
                    username=f"emailchange_{user.id}",
                    defaults={
                        "email": email,
                        "password": "",
                        "verification_code": code,
                        "expires_at": now + timedelta(minutes=2),
                        "is_verified": False,
                        "failed_attempts": 0,
                    }
                )
                temp.email = email
                temp.verification_code = code
                temp.expires_at = now + timedelta(minutes=2)
                temp.failed_attempts = 0
                temp.is_verified = False
                temp.save()
                email_sender.send(
                    subject="Verify your new email",
                    message=f"Your verification code is: {code}",
                    to=email
                )
                # stash payload and redirect to verify
                request.session["email_change_user_id"] = user.id
                request.session["email_change_new_email"] = email
                request.session["email_change_payload"] = {
                    "first_name": first_name or None,
                    "last_name": last_name or None,
                    "phone": phone or None,
                    "postal_code": postal_code or None,
                    "latitude": latitude,
                    "longitude": longitude,
                }
                messages.info(request, "We sent a verification code to your new email.")
                return redirect("verify_email")

            # required fields
            if not first_name or not last_name or not email or not phone or not bio:
                raise ValidationError("All fields are required.")
            # name validation
            if first_name:
                if len(first_name) < 2:
                    raise ValidationError("First name must be at least 2 characters.")
                user.first_name = first_name
            if last_name:
                if len(last_name) < 2:
                    raise ValidationError("Last name must be at least 2 characters.")
                user.last_name = last_name

            # persist profile fields (no location here)
            profile.phone = phone or profile.phone
            profile.postal_code = postal_code or profile.postal_code
            profile.bio = bio or "hi there! im using Freshbread."

            user.save()
            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")

        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, "freshbread/profile/pfe.html", {"user": user, "profile": profile, "values": values})
        except Exception as e:
            messages.error(request, "System error while saving profile.")
            return render(request, "freshbread/profile/pfe.html", {"user": user, "profile": profile, "values": values})

    return render(request, "freshbread/profile/pfe.html", {"user": user, "profile": profile, "values": values})

def public_user_profile(request, user_id: int):
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("index")
    from core.infrastructure.models import Profile
    prof = getattr(target, 'profile', None)
    if not prof:
        prof = Profile.objects.create(user=target)
    bio = prof.bio or "hi there! im using Freshbread."
    return render(request, "freshbread/profile/user_public.html", {"target": target, "profile": prof, "bio": bio})
