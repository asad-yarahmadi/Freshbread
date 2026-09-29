from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.interfaces.http.decorators import admin_login_protect
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
import random

@login_required
@admin_login_protect
def admin_order_reviews(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Not allowed.")
        return redirect("checkout_s1")
    from core.infrastructure.models import ManualOrderRequest, Profile
    pending = ManualOrderRequest.objects.filter(status='pending').order_by('-created_at')
    rejected = ManualOrderRequest.objects.filter(status='rejected').order_by('-updated_at')
    return render(request, "freshbread/admin/order_reviews.html", {
        "pending": pending,
        "rejected": rejected,
    })

@login_required
@admin_login_protect
@require_POST
def admin_order_accept(request, review_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Not allowed.")
        return redirect("admin_order_reviews")
    from core.infrastructure.models import ManualOrderRequest, UsedPaymentReference, Order, OrderItem, Product
    from core.application.services.badge_service import get_available_rewards, claim_reward
    import json
    from decimal import Decimal, InvalidOperation
    try:
        review = ManualOrderRequest.objects.get(id=review_id)
    except ManualOrderRequest.DoesNotExist:
        messages.error(request, "Review not found.")
        return redirect("admin_order_reviews")
    if UsedPaymentReference.objects.filter(reference=review.reference).exists():
        messages.error(request, "Reference already used.")
        return redirect("admin_order_reviews")
    UsedPaymentReference.objects.create(reference=review.reference, amount=review.total_due, email=review.email, user=review.user)
    import secrets
    order = Order.objects.create(user=review.user, status='processing', deliver=review.deliver, delivery_location=review.location, delivery_slot=review.delivery_slot, delivery_code=f"{random.randint(100000, 999999):06d}")
    items = json.loads(review.items_snapshot or '[]')
    for it in items:
        try:
            product = Product.objects.get(id=it.get('product_id'))
            saved_price = it.get('price', product.price)
            try:
                saved_price = Decimal(str(saved_price))
            except (InvalidOperation, TypeError, ValueError):
                saved_price = product.price
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int(it.get('quantity', 1)),
                price=saved_price,
            )
        except Exception:
            continue
    try:
        order.save()
    except Exception:
        pass
    review.status = 'accepted'
    review.save()
    # mark discount code as used (and delete) if present in review.reason
    try:
        reason_note = review.reason or ''
        if 'discount_code_id=' in reason_note:
            import re
            m = re.search(r'discount_code_id=(\d+)', reason_note)
            if m:
                dc_id = int(m.group(1))
                from django.utils import timezone
                from core.infrastructure.models import DiscountCode
                dc = DiscountCode.objects.filter(id=dc_id, owner=review.user).first()
                if dc:
                    if not dc.used_at:
                        dc.used_at = timezone.now()
                        dc.save(update_fields=['used_at'])
                    try:
                        dc.delete()
                    except Exception:
                        pass
    except Exception:
        pass
    
    # Claim available rewards
    try:
        available_rewards = get_available_rewards(review.user)
        for badge in available_rewards:
            claim_reward(review.user, badge, order)
    except Exception:
        pass

    try:
        if review.email:
            from core.infrastructure.email.email_sender import email_sender
            email_sender.send(
                subject='Order Accepted',
                message=f'Your order is accepted. Your Order Code: {order.order_code}. Delivery Code: {order.delivery_code}.',
                to=review.email,
                title='Order Accepted',
                wrap=True,
            )
    except Exception:
        pass
    messages.success(request, "Order accepted.")
    return redirect("admin_order_reviews")

@login_required
@admin_login_protect
@require_POST
def admin_order_reject(request, review_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Not allowed.")
        return redirect("admin_order_reviews")
    from core.infrastructure.models import ManualOrderRequest
    reason = (request.POST.get('reason') or '').strip()
    try:
        review = ManualOrderRequest.objects.get(id=review_id)
        review.status = 'rejected'
        review.reason = reason
        review.save()
        try:
            if review.email:
                from core.infrastructure.email.email_sender import email_sender
                email_sender.send(
                    subject='Order Rejected',
                    message=f'Your order was rejected. Reason: {reason}. You can try again. If something is wrong contact support.',
                    to=review.email,
                    title='Order Rejected',
                    wrap=True,
                )
        except Exception:
            pass
        messages.info(request, "Order rejected and user notified.")
    except ManualOrderRequest.DoesNotExist:
        messages.error(request, "Review not found.")
    return redirect("admin_order_reviews")

@login_required
@admin_login_protect
@require_POST
def admin_order_rejected_delete(request, review_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Not allowed.")
        return redirect("admin_order_reviews")
    from core.infrastructure.models import ManualOrderRequest
    ManualOrderRequest.objects.filter(id=review_id, status='rejected').delete()
    messages.info(request, "Rejected request deleted.")
    return redirect("admin_order_reviews")

@login_required
@admin_login_protect
def admin_notifications(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Not allowed.")
        return redirect("checkout_s1")
    from core.infrastructure.models import AdminNotification
    notes = AdminNotification.objects.filter(user=request.user, unread=True).order_by('-created_at')
    return render(request, "freshbread/admin/notifications.html", {"notifications": notes})

@login_required
@admin_login_protect
def admin_notification_open(request, notification_id):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Not allowed.")
        return redirect("checkout_s1")
    from core.infrastructure.models import AdminNotification
    try:
        note = AdminNotification.objects.get(id=notification_id, user=request.user)
        note.unread = False
        note.save()
        target = note.url or "admin_order_reviews"
        if target.startswith('/'):
            return redirect(target)
        return redirect(target)
    except AdminNotification.DoesNotExist:
        return redirect("admin_order_reviews")
