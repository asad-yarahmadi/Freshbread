from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.utils import timezone

from core.interfaces.http.decorators import cart_required, admin_login_protect
from core.application.services.cart_service import CartService
 
from core.infrastructure.models import Cart
import secrets
import re


# ─────────────────────────────────────────────
# STEP 1 – Select delivery & shipping
# ─────────────────────────────────────────────
@login_required
@cart_required
def checkout_s1(request):
    from core.infrastructure.models import Cart, Product, UserLocation, TempUser, DiscountCode

    items = []
    base_total = 0.0

    cart_items = Cart.objects.filter(user=request.user).select_related("product")
    for item in cart_items:
        items.append(item.product.name)
        base_total += float(item.product.price) * item.quantity

    if request.method == "POST":
        slot = request.POST.get("delivery_slot", "").strip()
        shipping = request.POST.get("shipping", "no").strip()
        loc_id = request.POST.get("location_id")
        discount_code = (request.POST.get("discount_code") or "").strip().upper()

        if not slot:
            messages.error(request, "Please select a delivery time.")
        elif shipping == "yes" and not loc_id:
            messages.error(request, "Please choose a delivery location.")
        else:
            temp_user, _ = TempUser.objects.get_or_create(
                email=request.user.email,
                defaults={
                    "username": request.user.username,
                    "password": secrets.token_urlsafe(16),
                    "verification_code": secrets.token_hex(3),
                    "expires_at": timezone.now() + timezone.timedelta(hours=2),
                    "ip": request.META.get("REMOTE_ADDR"),
                }
            )

            request.session["checkout_delivery_slot"] = slot
            request.session["checkout_shipping"] = shipping
            request.session["checkout_location_id"] = loc_id
            request.session.pop("checkout_discount_id", None)
            request.session.pop("checkout_discount_amount", None)
            if discount_code:
                dc = DiscountCode.objects.filter(code=discount_code, owner=request.user).first()
                if not dc or not dc.is_active():
                    messages.error(request, "Invalid or expired discount code.")
                    return redirect("checkout_s1")
                request.session["checkout_discount_id"] = dc.id
                request.session["checkout_discount_amount"] = float(dc.amount)
            request.session["temp_checkout"] = {
                "temp_user_id": temp_user.id,
                "step1_ok": True,
                "step2_ok": False,
            }
            payable_preview = base_total
            if shipping == "yes":
                payable_preview += 5.0
            disc_amount = float(request.session.get("checkout_discount_amount") or 0)
            payable_preview = max(0.0, payable_preview - disc_amount)
            if disc_amount > 0 and payable_preview <= 0:
                request.session["temp_checkout"]["step2_ok"] = True
                request.session["payment_audit"] = {"status": "discount_full", "last_reference": ""}
                # create admin manual order request automatically
                from core.infrastructure.models import Cart as CartModel, AdminNotification, ManualOrderRequest
                items = CartModel.objects.filter(user=request.user).select_related("product")
                snapshot = []
                total = 0.0
                for it in items:
                    snapshot.append({
                        "product_id": it.product.id,
                        "name": it.product.name,
                        "price": float(it.product.price),
                        "quantity": it.quantity,
                    })
                    total += float(it.product.price) * it.quantity
                if shipping == "yes":
                    total += 5.0
                import json
                ref = secrets.token_hex(6).upper()
                loc = None
                if shipping == "yes":
                    try:
                        from core.infrastructure.models import UserLocation
                        loc_id = request.session.get("checkout_location_id")
                        if loc_id:
                            loc = UserLocation.objects.filter(id=loc_id, user=request.user).first()
                    except Exception:
                        loc = None
                reason = None
                try:
                    dc_id = request.session.get("checkout_discount_id")
                    if dc_id:
                        reason = f"discount_code_id={dc_id};amount={disc_amount}"
                except Exception:
                    reason = None
                mor = ManualOrderRequest.objects.create(
                    user=request.user,
                    email=request.user.email or "",
                    reference=ref,
                    total_due=max(0.0, total - disc_amount),
                    deliver=(shipping == "yes"),
                    location=loc,
                    delivery_slot=(slot or None),
                    items_snapshot=json.dumps(snapshot),
                    status="pending",
                    reason=reason,
                )
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    for admin in User.objects.filter(is_staff=True):
                        note_msg = f"New free order request from {request.user.username} (ref {ref})"
                        if disc_amount > 0:
                            note_msg += f" – discount used ${disc_amount:.2f}"
                        AdminNotification.objects.create(
                            user=admin,
                            message=note_msg,
                            url=f"/admin/order_reviews/?rid={mor.id}"
                        )
                except Exception:
                    pass
                messages.success(request, "Your free order request has been submitted for admin review.")
                request.session["payment_verified"] = True
                request.session["verified_reference"] = ref
                return redirect("checkout_success")
            return redirect("checkout_s2")

    locations = UserLocation.objects.filter(user=request.user).order_by("-updated_at")

    context = {
        "cart_items_names": items,
        "base_total": round(base_total, 2),
        "locations": locations,
        "shipping_charge": 5.00,
        "discount_code_applied": bool(request.session.get("checkout_discount_id")),
    }
    return render(request, "freshbread/checkout/checkout_s1.html", context)


# ─────────────────────────────────────────────
# STEP 2 – Payment instructions
# ─────────────────────────────────────────────
@login_required
@cart_required
def checkout_s2(request):
    temp = request.session.get("temp_checkout") or {}
    if not temp.get("step1_ok"):
        messages.error(request, "Please complete step 1.")
        return redirect("checkout_s1")

    summary = CartService.get_cart_summary(request)
    total_due = float(summary.get("total", 0))

    if request.session.get("checkout_shipping") == "yes":
        total_due += 5.0
    disc_amount = float(request.session.get("checkout_discount_amount") or 0)
    total_due = max(0.0, total_due - disc_amount)

    return render(
        request,
        "freshbread/checkout/checkout_s2.html",
        {
            "site_email": request.user.email,
            "payable": round(total_due, 2),
            "discount_amount": disc_amount,
        }
    )


# ─────────────────────────────────────────────
# STEP 2 – Verify payment inbox
# ─────────────────────────────────────────────
@login_required
@require_POST
@cart_required
def checkout_paid(request):
    temp = request.session.get("temp_checkout") or {}
    temp["step2_ok"] = True
    request.session["temp_checkout"] = temp
    request.session["payment_audit"] = {"status": "pending_review", "last_reference": ""}
    return redirect("checkout_s3")


# ─────────────────────────────────────────────
# STEP 3 – Confirm reference number
# ─────────────────────────────────────────────
@login_required
@cart_required
def checkout_s3(request):
    temp = request.session.get("temp_checkout") or {}
    audit = request.session.get("payment_audit") or {}
    if not temp.get("step2_ok"):
        messages.error(request, "Please complete step 2.")
        return redirect("checkout_s2")

    summary = CartService.get_cart_summary(request)
    total_due = float(summary.get("total", 0))
    if request.session.get("checkout_shipping") == "yes":
        total_due += 5.0
    disc_amount = float(request.session.get("checkout_discount_amount") or 0)
    total_due = max(0.0, total_due - disc_amount)

    if request.method == "POST":
        ref = request.POST.get("reference", "").strip()
        if len(ref) != 12:
            messages.error(request, " Invalid Reference Number.")
            return redirect("checkout_s3")
        from core.infrastructure.models import UsedPaymentReference
        if UsedPaymentReference.objects.filter(reference=ref).exists():
            messages.error(request, "Wrong reference number.")
            return redirect("checkout_s3")
        from core.infrastructure.models import ManualOrderRequest
        recent_cutoff = timezone.now() - timezone.timedelta(minutes=2)
        if ManualOrderRequest.objects.filter(user=request.user, created_at__gte=recent_cutoff, status='pending').exists():
            messages.error(request, "You submitted a request recently. Please wait 2 minutes before trying again.")
            return redirect("checkout_s3")
        if ManualOrderRequest.objects.filter(reference=ref, status='pending').exists():
            messages.error(request, "This Reference Number is already under review.")
            return redirect("checkout_s3")
        # Create pending manual review for admin
        from core.infrastructure.models import Cart, AdminNotification
        items = Cart.objects.filter(user=request.user).select_related("product")
        snapshot = []
        total = 0.0
        for it in items:
            snapshot.append({
                "product_id": it.product.id,
                "name": it.product.name,
                "price": float(it.product.price),
                "quantity": it.quantity,
            })
            total += float(it.product.price) * it.quantity
        if request.session.get("checkout_shipping") == "yes":
            total += 5.0
        import json
        # attach location if delivery requested
        loc = None
        if request.session.get("checkout_shipping") == "yes":
            try:
                from core.infrastructure.models import UserLocation
                loc_id = request.session.get("checkout_location_id")
                if loc_id:
                    loc = UserLocation.objects.filter(id=loc_id, user=request.user).first()
            except Exception:
                loc = None
        reason = None
        try:
            dc_id = request.session.get("checkout_discount_id")
            if dc_id and disc_amount > 0:
                reason = f"discount_code_id={dc_id};amount={disc_amount}"
        except Exception:
            reason = None
        mor = ManualOrderRequest.objects.create(
            user=request.user,
            email=request.user.email or "",
            reference=ref,
            total_due=max(0.0, total - disc_amount),
            deliver=(request.session.get("checkout_shipping") == "yes"),
            location=loc,
            delivery_slot=(request.session.get("checkout_delivery_slot") or None),
            items_snapshot=json.dumps(snapshot),
            status="pending",
            reason=reason,
        )
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for admin in User.objects.filter(is_staff=True):
                note_msg = f"New order request from {request.user.username} (ref {ref})"
                if disc_amount > 0:
                    note_msg += f" – discount used ${disc_amount:.2f}"
                AdminNotification.objects.create(
                    user=admin,
                    message=note_msg,
                    url=f"/admin/order_reviews/?rid={mor.id}"
                )
        except Exception:
            pass
        request.session["payment_verified"] = True
        request.session["verified_reference"] = ref
        msg = "We are checking your request as soon as possible. Please check your email for the result."
        if disc_amount > 0:
            msg += " Discount applied: $%s." % ("%.2f" % disc_amount)
        messages.success(request, msg)
        return redirect("checkout_success")

    return render(
        request,
        "freshbread/checkout/checkout_s3.html",
        {"payable": round(total_due, 2)}
    )


# ─────────────────────────────────────────────
# Cancel checkout safely
# ─────────────────────────────────────────────
@login_required
@require_POST
def checkout_cancel(request):
    for key in [
        "checkout_delivery_slot",
        "checkout_shipping",
        "checkout_location_id",
        "temp_checkout",
        "payment_audit",
    ]:
        request.session.pop(key, None)

    messages.info(request, "Checkout canceled.")
    return redirect("reservation")


# ─────────────────────────────────────────────
# AJAX – verify payment status
# ─────────────────────────────────────────────


@login_required
def checkout_success(request):
    if not request.user.is_authenticated:
        return redirect("checkout_s1")   # یا هر صفحه‌ای که می‌خوای

    from core.infrastructure.models import Cart
    Cart.objects.filter(user=request.user).delete()

    # فقط کلیدهای مربوط به checkout رو پاک کن (نه کل session)
    keys_to_remove = [
        "checkout_delivery_slot",
        "checkout_shipping",
        "checkout_location_id",
        "temp_checkout",
        "payment_audit", 
        "checkout_discount_id",
        "checkout_discount_amount",
    ]

    # clear session keys after success
    for key in keys_to_remove:
        request.session.pop(key, None)
    return render(request, "freshbread/checkout/success.html")


