from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg

from ..decorators import admin_login_protect

def about(request):
    from core.infrastructure.repositories.product_repository import ProductRepository
    products = ProductRepository.get_all_products(available_only=True)
    return render(request, 'freshbread/ecommerce/about.html', {'products': products})

def contact(request):
    return render(request, 'freshbread/ecommerce/contact.html')

def gallery(request):
    from core.infrastructure.models import GalleryImage
    images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'freshbread/ecommerce/gallery.html', {"images": images})

def index(request):
    from core.infrastructure.repositories.product_repository import ProductRepository
    from core.infrastructure.models import GalleryImage

    products = ProductRepository.get_all_products(available_only=True)[:50]
    hero_images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')[:5]
    images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')[:6]

    return render(request, "freshbread/ecommerce/index.html", {
        "products": products,
        "hero_images": hero_images,
        "images": images
    })

def menu(request):
    from core.infrastructure.repositories.product_repository import ProductRepository
    products = ProductRepository.get_all_products(available_only=True)
    return render(request, 'freshbread/ecommerce/menu.html', {'products': products})

def reverse_geocode(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
    headers = {"User-Agent": "FreshBreadApp/1.0 (contact@freshbread.com)"}
    import requests
    try:
        res = requests.get(url, headers=headers, timeout=5)
        return JsonResponse(res.json())
    except Exception as e:
        return JsonResponse({"error": "Failed to reverse geocode", "details": str(e)}, status=500)

def stuff(request):
    from django.http import HttpResponse

    return render (request, 'freshbread/ecommerce/stuff.html')


def food_de(request, slug):
    from core.infrastructure.models import Product as ProductModel, Cart as CartModel
    product = get_object_or_404(ProductModel, slug=slug, available=True)
    cart_quantity = 0
    if request.user.is_authenticated:
        cart_item = CartModel.objects.filter(user=request.user, product=product).first()
        if cart_item:
            cart_quantity = cart_item.quantity
    else:
        cart = request.session.get('cart', {})
        if str(product.slug) in cart:
            cart_quantity = cart[str(product.slug)].get('quantity', 0)
    approved_reviews = product.reviews.filter(is_approved=True)
    avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    context = {
        'product': product,
        'cart_quantity': cart_quantity,
        'approved_reviews': approved_reviews,
        'avg_rating': round(avg_rating, 1),
        'approved_reviews_count': approved_reviews.count(),
    }
    return render(request, 'freshbread/fd.html', context)

def prpo (request):
    return render(request, 'freshbread/ecommerce/prpo.html')

def tms (request):
    return render(request, 'freshbread/ecommerce/tms.html')

def coming_soon (request):
    return render(request, 'freshbread/ecommerce/coming_soon.html')

from django.http import JsonResponse
from django.utils import timezone
import datetime

def get_countdown_data(request):
    # تاریخ پایان (naive اول، بعد aware می‌کنیم)
    end_date_naive = datetime.datetime(2026, 1, 30, 23, 59, 0)
    end_date = timezone.make_aware(
        end_date_naive,
        timezone=timezone.get_current_timezone()
    )

    time_remaining = end_date - timezone.now()
    if time_remaining.total_seconds() < 0:
        time_remaining = timezone.timedelta(0)

    data = {
        "year": end_date.year,
        "month": end_date.month,
        "day": end_date.day,
        "hour": end_date.hour,
        "minute": end_date.minute,
        "second": end_date.second,
        "total_seconds_left": int(time_remaining.total_seconds()),
    }

    return JsonResponse(data)


