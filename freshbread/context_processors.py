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

def announcement_and_release(request):
    from core.infrastructure.models import SiteAnnouncement, ReleaseNote
    from django.utils import timezone
    announcement = None
    release_to_show = None
    current_version = ""
    recent_releases = []
    try:
        announcement = SiteAnnouncement.objects.filter(is_active=True).order_by("-created_at").first()
        if announcement and getattr(announcement, "show_once", True):
            key = f"ann_seen_{announcement.id}"
            if request.session.get(key):
                announcement = None
            else:
                request.session[key] = True
    except Exception:
        announcement = None
    try:
        qs = ReleaseNote.objects.filter(published=True).order_by("-release_date", "-created_at")
        recent_releases = list(qs[:8])
        if recent_releases:
            current_version = recent_releases[0].version
            key_r = f"release_seen_{recent_releases[0].version}"
            if not request.session.get(key_r):
                release_to_show = recent_releases[0]
                request.session[key_r] = True
    except Exception:
        current_version = ""
        recent_releases = []
    return {
        "announcement": announcement,
        "release_to_show": release_to_show,
        "current_version": current_version,
        "recent_releases": recent_releases,
    }
# کلاس مدل SiteLock را ایمپورت کنید (نه فیلد reason)
from core.infrastructure.models.site_lock import SiteLock

def site_lock_reason(request):
    # حالا می‌توانید از SiteLock.objects استفاده کنید
    # فرض می‌کنیم فقط یک رکورد برای قفل سایت دارید
    site_lock_obj = SiteLock.objects.first()
    
    return {
        'site_lock': site_lock_obj
    }