from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def order_detail(request, order_code):
    from core.infrastructure.repositories.order_repository import OrderRepository
    from core.infrastructure.models import ClaimedBadgeReward
    order = OrderRepository.get_order_by_code(order_code)
    if not order:
        messages.error(request, "Order not found.")
        return redirect('profile')
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, "Order not found.")
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
    claimed_rewards = ClaimedBadgeReward.objects.filter(order=order).select_related('badge')
    return render(request, "freshbread/order/order_info1.html", {"order": order, "discount_used": discount_used, "claimed_rewards": claimed_rewards})

@login_required
def cancel_order(request, order_id):
    from core.application.services.order_service import OrderService
    try:
        OrderService.cancel_order(order_id, request.user)
        messages.warning(request, "Order cancelled.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('manage_orders')

