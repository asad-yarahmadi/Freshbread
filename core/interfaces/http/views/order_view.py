from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..decorators import admin_login_protect
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
import random
@login_required
@admin_login_protect
def manage_orders(request):
    from core.infrastructure.repositories.order_repository import OrderRepository
    from django.db.models import Q
    orders = OrderRepository.get_all_orders()
    by = request.GET.get('by')
    q = (request.GET.get('q') or '').strip()
    sort = request.GET.get('sort')
    if q:
        if by == 'name':
            orders = orders.filter(Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q))
        elif by == 'username':
            orders = orders.filter(user__username__icontains=q)
        elif by == 'code':
            orders = orders.filter(order_code__icontains=q)
    if sort == 'date_asc':
        orders = orders.order_by('created_at')
    elif sort == 'date_desc':
        orders = orders.order_by('-created_at')
    elif sort == 'total_asc':
        orders = orders.order_by('total_price')
    elif sort == 'total_desc':
        orders = orders.order_by('-total_price')
    else:
        orders = orders.order_by('created_at')
    # new_orders = orders.exclude(status__in=["delivered", "cancelled"])
    # sent_orders = orders.filter(status__in=["sending", "delivered"])
    # cancelled_orders = orders.filter(status="cancelled")

    return render(request, 'freshbread/order/order_manage.html', {'orders': orders, 'by': by, 'q': q, 'sort': sort})

@login_required
@admin_login_protect
def deliver_verify(request, order_id):
    from core.infrastructure.repositories.order_repository import OrderRepository
    order = OrderRepository.get_order_by_id(order_id)
    if not order:
        messages.error(request, "Order not found.")
        return redirect('manage_orders')
    if request.method == 'POST':
        code = (request.POST.get('delivery_code') or '').strip().upper()
        if not code:
            messages.error(request, "Please enter delivery code.")
            return redirect('deliver_verify', order_id=order_id)
        if code != (order.delivery_code or ''):
            messages.error(request, "Wrong delivery code. Please try again.")
            return redirect('deliver_verify', order_id=order_id)
        from core.infrastructure.repositories.order_repository import OrderRepository
        ok = False
        try:
            ok = OrderRepository.update_order_status(order.id, 'delivered')
        except Exception as e:
            messages.error(request, f"Failed to update: {str(e)}")
            return redirect('manage_orders')
        if ok:
            messages.success(request, "Order marked as delivered.")
            return redirect('delivered_list')
        try:
            from django.utils import timezone
            from core.infrastructure.models import Order as OrderModel, ReferralRecord, DiscountCode, Profile
            OrderModel.objects.filter(id=order.id).update(status='delivered', completed_at=timezone.now())
            rr_qs = ReferralRecord.objects.filter(used_by=order.user, has_order=False)
            owner_ids = list(rr_qs.values_list('owner_id', flat=True))
            rr_qs.update(has_order=True)
            for oid in owner_ids:
                count = ReferralRecord.objects.filter(owner_id=oid, has_order=True).count()
                step = 7
                target_awards = count // step
                current_awards = DiscountCode.objects.filter(owner_id=oid, amount=50.00).count()
                to_issue = max(0, target_awards - current_awards)
                for _ in range(to_issue):
                    import secrets
                    code = secrets.token_hex(4).upper()
                    expires = timezone.now() + timezone.timedelta(days=14)
                    DiscountCode.objects.create(code=code, owner_id=oid, amount=50.00, expires_at=expires)
                    try:
                        from django.contrib.auth import get_user_model
                        from core.infrastructure.email.email_sender import email_sender
                        User = get_user_model()
                        owner = User.objects.get(id=oid)
                        if owner.email:
                            reason_text = "Thank you for sharing Fresh Bread with friends."
                            reason_text += " You earned a $50 discount because your referrals completed their orders."
                            html_msg = f"<p>{reason_text}</p><p>Your discount code: <strong>{code}</strong></p><p>This code expires in 14 days.</p>"
                            email_sender.send(
                                subject="Thank you! Your $50 discount code",
                                message=f"{reason_text}\nYour discount code: {code}\nThis code expires in 14 days.",
                                to=owner.email,
                                html_message=html_msg,
                                title="Your $50 Discount Code",
                                wrap=True,
                            )
                    except Exception:
                        pass
                Profile.objects.filter(user_id=oid).update(referral_used_count=count)
            messages.success(request, "Order marked as delivered.")
            return redirect('delivered_list')
        except Exception:
            messages.error(request, "Failed to update order status.")
            return redirect('manage_orders')
    return render(request, 'freshbread/order/deliver_verify.html', {'order': order})

@login_required
@admin_login_protect
def delivered_list(request):
    from core.infrastructure.repositories.order_repository import OrderRepository
    orders = OrderRepository.get_orders_by_status('delivered')
    return render(request, 'freshbread/order/delivered_list.html', {'orders': orders})

@login_required
@admin_login_protect
def update_order_status(request, order_id, new_status):
    from core.application.services.order_service import OrderService
    try:
        OrderService.update_order_status(order_id, new_status)
        messages.success(request, "Order updated.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('manage_orders')

@login_required
@admin_login_protect
def cancel_order(request, order_id):
    from core.application.services.order_service import OrderService
    try:
        OrderService.cancel_order(order_id, request.user)
        messages.warning(request, "Order cancelled.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('manage_orders')

@login_required
@admin_login_protect
def order_info(request, order_id):
    from core.infrastructure.repositories.order_repository import OrderRepository
    order = OrderRepository.get_order_by_id(order_id)
    discount_used = None
    try:
        from django.utils import timezone
        from core.infrastructure.models import DiscountCode
        window_start = (order.created_at or timezone.now()) - timezone.timedelta(hours=2)
        window_end = (order.created_at or timezone.now()) + timezone.timedelta(hours=2)
        discount_used = DiscountCode.objects.filter(owner=order.user, used_at__isnull=False, used_at__gte=window_start, used_at__lte=window_end).order_by('-used_at').first()
    except Exception:
        discount_used = None
    return render(request, 'freshbread/order/order_info.html', {'order': order, 'discount_used': discount_used})

@login_required
def order_detail(request, order_code):
    from core.infrastructure.repositories.order_repository import OrderRepository
    order = OrderRepository.get_order_by_code(order_code)
    if not order:
        messages.error(request, "Order not found.")
        return redirect('profile')
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, "You are not allowed to view this order.")
        raise PermissionError
    discount_used = None
    try:
        from django.utils import timezone
        from core.infrastructure.models import DiscountCode
        window_start = (order.created_at or timezone.now()) - timezone.timedelta(hours=2)
        window_end = (order.created_at or timezone.now()) + timezone.timedelta(hours=2)
        discount_used = DiscountCode.objects.filter(owner=order.user, used_at__isnull=False, used_at__gte=window_start, used_at__lte=window_end).order_by('-used_at').first()
    except Exception:
        discount_used = None
    return render(request, "freshbread/order/order_info1.html", {"order": order, "discount_used": discount_used})

@login_required
def locations_manage_view(request):
    from core.infrastructure.models import UserLocation
    locations = list(UserLocation.objects.filter(user=request.user).order_by('-updated_at'))
    return render(request, 'freshbread/order/locations_manage.html', { 'locations': locations })

@login_required
def location_add_view(request):
    from core.infrastructure.models import UserLocation, Profile
    from django.core.exceptions import ValidationError
    import requests
    if request.method == 'POST':
        addr = request.POST.get('address_line', '').strip()
        postal = request.POST.get('postal_code', '').strip()
        house = request.POST.get('house_number', '').strip()
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        receiver_is_user = request.POST.get('receiver_is_user') == 'on'
        receiver_name = request.POST.get('receiver_name', '').strip()
        receiver_phone = request.POST.get('receiver_phone', '').strip()
        try:
            if not lat or not lng:
                raise ValidationError('Please choose a location on the map.')
            # validate Ottawa street
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {"User-Agent": "FreshBreadApp/1.0 (contact@freshbread.com)"}
            info = requests.get(url, headers=headers, timeout=5).json()
            a = info.get('address', {})
            if not ((a.get('road') or a.get('pedestrian') or a.get('cycleway') or a.get('footway')) and a.get('city') == 'Ottawa'):
                raise ValidationError('Location must be on a street within Ottawa.')
            # lock fields after map
            if not addr or not postal or not house:
                raise ValidationError('Address, postal code, and house number are required.')
            if receiver_is_user:
                receiver_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                prof = Profile.objects.filter(user=request.user).first()
                receiver_phone = (prof.phone if prof else '') or receiver_phone
            else:
                # basic validations
                if len(receiver_name) < 2:
                    raise ValidationError('Receiver name must be at least 2 characters.')
                if len(receiver_phone) < 7:
                    raise ValidationError('Receiver phone must be at least 7 digits.')
            UserLocation.objects.create(
                user=request.user,
                receiver_is_user=receiver_is_user,
                receiver_name=receiver_name or None,
                receiver_phone=receiver_phone or None,
                address_line=addr,
                postal_code=postal,
                house_number=house,
                latitude=lat,
                longitude=lng,
            )
            messages.success(request, 'Location added successfully.')
            return redirect('locations_manage')
        except ValidationError as e:
            messages.error(request, str(e))
    return render(request, 'freshbread/order/location_add.html')

@login_required
def location_edit_view(request, pk):
    from core.infrastructure.models import UserLocation
    import requests
    loc = UserLocation.objects.filter(id=pk, user=request.user).first()
    if not loc:
        messages.error(request, 'Location not found.')
        return redirect('locations_manage')
    if request.method == 'POST':
        addr = request.POST.get('address_line', '').strip()
        postal = request.POST.get('postal_code', '').strip()
        house = request.POST.get('house_number', '').strip()
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        receiver_is_user = request.POST.get('receiver_is_user') == 'on'
        receiver_name = request.POST.get('receiver_name', '').strip()
        receiver_phone = request.POST.get('receiver_phone', '').strip()
        try:
            if not lat or not lng:
                raise ValidationError('Please choose a location on the map.')
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {"User-Agent": "FreshBreadApp/1.0 (contact@freshbread.com)"}
            info = requests.get(url, headers=headers, timeout=5).json()
            a = info.get('address', {})
            if not ((a.get('road') or a.get('pedestrian') or a.get('cycleway') or a.get('footway')) and a.get('city') == 'Ottawa'):
                raise ValidationError('Location must be on a street within Ottawa.')
            if not addr or not postal or not house:
                raise ValidationError('Address, postal code, and house number are required.')
            loc.receiver_is_user = receiver_is_user
            loc.receiver_name = receiver_name or None
            loc.receiver_phone = receiver_phone or None
            loc.address_line = addr
            loc.postal_code = postal
            loc.house_number = house
            loc.latitude = lat
            loc.longitude = lng
            loc.save()
            messages.success(request, 'Location updated.')
            return redirect('locations_manage')
        except ValidationError as e:
            messages.error(request, str(e))
    return render(request, 'freshbread/order/location_add.html', { 'edit': True, 'location': loc })

@login_required
def location_delete_view(request, pk):
    from core.infrastructure.models import UserLocation
    loc = UserLocation.objects.filter(id=pk, user=request.user).first()
    if not loc:
        messages.error(request, 'Location not found.')
    else:
        loc.delete()
        messages.success(request, 'Location deleted.')
    return redirect('locations_manage')

# ─────────────────────────────────────────────
# Admin – Manage manual order requests
# ─────────────────────────────────────────────
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
    import json
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
            OrderItem.objects.create(order=order, product=product, quantity=int(it.get('quantity', 1)), price=product.price)
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
            from django.core.mail import send_mail
            if review.email:
                send_mail(
                    subject='Order Rejected',
                    message=f'Your order was rejected. Reason: {reason}. You can try again. If something is wrong contact support.',
                    from_email=None,
                    recipient_list=[review.email],
                    fail_silently=True,
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
