def cart_total_items(request):
    # Lazy import to avoid AppRegistry issues
    from core.infrastructure.models import Cart
    from django.db.models import F

    if getattr(request, 'user', None) and request.user.is_authenticated:
        total_items = sum(
            item.quantity
            for item in Cart.objects.filter(user=request.user).select_related('product')
            if getattr(item.product, 'available', True)
        )
    else:
        cart = request.session.get('cart', {})
        total_items = sum(item.get('quantity', 0) for item in cart.values())

    return {'total_items': total_items}

def cart_context(request):
    from core.infrastructure.models import Cart as CartModel, Product as ProductModel

    total_items = 0
    cart_total = 0.0
    cart_items = []

    if request.user.is_authenticated:
        cart_items = list(
            CartModel.objects
            .filter(user=request.user)
            .select_related('product')
            .order_by('-added_at')
        )
        for item in cart_items:
            if getattr(item.product, 'available', True):
                cart_total += float(item.product.price) * item.quantity
                total_items += item.quantity

    else:
        session_cart = request.session.get("cart", {})
        for slug, data in session_cart.items():
            try:
                product = ProductModel.objects.get(slug=slug, available=True)
                price = float(product.price)
                cart_total += price * data["quantity"]
                total_items += data["quantity"]
            except ProductModel.DoesNotExist:
                continue

    return {
        "cart_items": cart_items,
        "total_items": total_items,
        "cart_total": round(cart_total, 2),
    }
