from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
def add_to_cart(request, slug, quantity=1):
    from core.application.services.cart_service import CartService
    try:
        result = CartService.add_to_cart(request, slug, int(quantity))
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'quantity': result['quantity']})
        return redirect('cart')
    except Exception as e:
        messages.error(request, str(e))
        return redirect('cart')

def update_cart(request):
    from django.views.decorators.http import require_POST
    from django.utils.decorators import method_decorator
    from core.infrastructure.repositories.product_repository import ProductRepository
    from core.infrastructure.repositories.cart_repository import CartRepository
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    import json
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    product_id = data.get("product_id")
    action = data.get("action")
    product = ProductRepository.get_product_by_id(product_id)
    if not product:
        return JsonResponse({"error": "Product not found"}, status=404)
    cart, _ = CartRepository.get_or_create_user_cart(request.user)
    if action == "add":
        CartRepository.add_or_update_cart_item(request.user, product, 1)
    elif action == "remove":
        CartRepository.decrement_cart_item(request.user, product)
    elif action == "delete":
        item = CartRepository.get_cart_item(request.user, product)
        if item:
            CartRepository.remove_cart_item(item)
    return JsonResponse({"status": "ok", "product": product.name})


def reservation(request):
    from core.application.services.cart_service import CartService
    from core.infrastructure.models import Profile
    import random, string
    summary = CartService.get_cart_summary(request)
    cart_items = summary['cart_items']
    transformed = []
    for item in cart_items:
        transformed.append({
            'id': item.get('id'),
            'product': item['product'],
            'quantity': item['quantity'],
            'total_price': item['total_price'] if 'total_price' in item else item['price'] * item['quantity']
        })
    referral_code = None
    referral_orders_count = None
    prof = Profile.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if prof:
        if not prof.referral_code:
            rc = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            while Profile.objects.filter(referral_code=rc).exists():
                rc = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            prof.referral_code = rc
            prof.save(update_fields=['referral_code'])
        referral_code = prof.referral_code
        referral_orders_count = int(getattr(prof, 'referral_used_count', 0) or 0)
    next_reward_in = None
    if referral_orders_count is not None:
        step = 7
        next_reward_in = ((referral_orders_count // step) + 1) * step - referral_orders_count if referral_orders_count >= 0 else step
    return render(request, 'freshbread/cart/reservation.html', {
        'cart_items': transformed,
        'original_total': summary['original_total'],
        'savings': summary['savings'],
        'total': summary['total'],
        'referral_code': referral_code,
        'referral_orders_count': referral_orders_count,
        'next_reward_in': next_reward_in,
    })

def remove_from_cart(request, item_id):
    from core.application.services.cart_service import CartService
    try:
        CartService.remove_from_cart(request, item_id)
        messages.info(request, "🗑️ item removed from cart.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('view_cart')

def set_cart_quantity(request, slug, quantity):
    from core.application.services.cart_service import CartService
    try:
        result = CartService.set_cart_quantity(request, slug, int(quantity))
        return JsonResponse({
            'success': True,
            'quantity': result['quantity'],
            'total': result.get('total'),
            'original_total': result.get('original_total'),
            'savings': result.get('savings'),
            'message': result.get('message')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

