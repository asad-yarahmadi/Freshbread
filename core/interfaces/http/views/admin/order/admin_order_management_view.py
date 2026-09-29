from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.interfaces.http.decorators import admin_login_protect

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
                            reason_text = "Thank you for sharing Kingfood with friends."
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
def order_info(request, order_id):
    from core.infrastructure.repositories.order_repository import OrderRepository
    from core.infrastructure.models import ClaimedBadgeReward
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
    claimed_rewards = ClaimedBadgeReward.objects.filter(order=order).select_related('badge')
    return render(request, 'freshbread/order/order_info.html', {'order': order, 'discount_used': discount_used, 'claimed_rewards': claimed_rewards})
