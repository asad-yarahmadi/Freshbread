from django.core.cache import cache

def cart_total_items(request):
    """
    استفاده مستقیم از همان مقداری که cart_context محاسبه کرده 
    یا محاسبه سریع بدون کوئری اضافه.
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        # اگر cart_context قبلاً اجرا شده باشد، از دیتابیس مجدد نمی‌خواند
        return cart_context(request)
    
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
        if session_cart:
            # بهینه‌سازی مهم: بجای N کوئری داخل حلقه، همه محصولات در ۱ کوئری خوانده می‌شوند
            slugs = list(session_cart.keys())
            products = ProductModel.objects.filter(slug__in=slugs, available=True).in_bulk(field_name='slug')
            
            for slug, data in session_cart.items():
                product = products.get(slug)
                if product:
                    price = float(product.price)
                    cart_total += price * data.get("quantity", 0)
                    total_items += data.get("quantity", 0)

    return {
        "cart_items": cart_items,
        "total_items": total_items,
        "cart_total": round(cart_total, 2),
    }


def announcement_and_release(request):
    from core.infrastructure.models import SiteAnnouncement, ReleaseNote

    # ۱. خواندن اعلان کش‌شده (به مدت ۱۰ دقیقه در Redis)
    announcement = cache.get("global_active_announcement")
    if announcement is None:
        try:
            announcement = SiteAnnouncement.objects.filter(is_active=True).order_by("-created_at").first()
            cache.set("global_active_announcement", announcement, 600)
        except Exception:
            announcement = None

    # بررسی نمایش تک‌باره (Show Once) از روی Session
    if announcement and getattr(announcement, "show_once", True):
        key = f"ann_seen_{announcement.id}"
        if request.session.get(key):
            announcement = None
        else:
            request.session[key] = True

    # ۲. خواندن Release Notes کش‌شده (به مدت ۳۰ دقیقه در Redis)
    recent_releases = cache.get("global_recent_releases")
    if recent_releases is None:
        try:
            qs = ReleaseNote.objects.filter(published=True).order_by("-release_date", "-created_at")
            recent_releases = list(qs[:8])
            cache.set("global_recent_releases", recent_releases, 1800)
        except Exception:
            recent_releases = []

    release_to_show = None
    current_version = ""

    if recent_releases:
        current_version = recent_releases[0].version
        key_r = f"release_seen_{current_version}"
        if not request.session.get(key_r):
            release_to_show = recent_releases[0]
            request.session[key_r] = True

    return {
        "announcement": announcement,
        "release_to_show": release_to_show,
        "current_version": current_version,
        "recent_releases": recent_releases,
    }


def site_lock_reason(request):
    from core.infrastructure.models.site_lock import SiteLock

    # وضعیت قفل سایت به مدت ۵ دقیقه کش می‌شود (حذف ۱ کوئری در تمام صفحات)
    site_lock_obj = cache.get("global_site_lock")
    if site_lock_obj is None:
        try:
            site_lock_obj = SiteLock.objects.first()
            cache.set("global_site_lock", site_lock_obj, 300)
        except Exception:
            site_lock_obj = None

    return {
        'site_lock': site_lock_obj
    }