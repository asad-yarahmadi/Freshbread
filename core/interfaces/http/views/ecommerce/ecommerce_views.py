from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import JsonResponse
from django.utils import timezone
import datetime
import requests

def about(request):
    from core.infrastructure.repositories.product_repository import ProductRepository
    products = ProductRepository.get_all_products(available_only=True)
    return render(request, 'ecommerce/about.html', {'products': products})

def contact(request):
    return render(request, 'ecommerce/contact.html')

def gallery(request):
    from core.infrastructure.models import GalleryImage
    images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'ecommerce/gallery.html', {"images": images})

def index(request):
    from core.infrastructure.repositories.product_repository import ProductRepository
    from core.infrastructure.repositories.slideshow_repository import SlideshowRepository
    from core.infrastructure.models import GalleryImage

    products = ProductRepository.get_all_products()[:50]
    hero_images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')[:5]
    images = GalleryImage.objects.filter(is_active=True).order_by('-created_at')[:6]

    slideshow_mode = SlideshowRepository.get_active_slideshow()
    slides = []
    use_custom = False
    if slideshow_mode and not slideshow_mode.is_default:
        slides = slideshow_mode.slides.prefetch_related('buttons').all()
        use_custom = True

    return render(request, "ecommerce/index.html", {
        "products": products,
        "hero_images": hero_images,
        "images": images,
        "slideshow_mode": slideshow_mode,
        "slides": slides,
        "use_custom_slideshow": use_custom
    })

def menu(request):
    from core.infrastructure.repositories.product_repository import ProductRepository
    products = ProductRepository.get_all_products()
    return render(request, 'ecommerce/menu.html', {'products': products})

def reverse_geocode(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse(
            {"error": "Latitude and longitude are required."},
            status=400,
        )

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return JsonResponse(
            {"error": "Invalid latitude or longitude."},
            status=400,
        )

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return JsonResponse(
            {"error": "Latitude or longitude is out of range."},
            status=400,
        )

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "en",
    }

    headers = {
        "User-Agent": "KingFood/1.0 (https://kingfood.ca/)",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=5,
        )

        response.raise_for_status()

        return JsonResponse(response.json())

    except requests.RequestException:
        return JsonResponse(
            {"error": "Reverse geocoding service is temporarily unavailable."},
            status=502,
        )

def stuff(request):
    from django.http import HttpResponse

    return render (request, 'ecommerce/stuff.html')


def food_de(request, slug):
    from core.infrastructure.models import Product as ProductModel, Cart as CartModel
    product = get_object_or_404(ProductModel, slug=slug)
    cart_quantity = 0
    if request.user.is_authenticated:
        cart_item = CartModel.objects.filter(user=request.user, product=product).first()
        if cart_item:
            cart_quantity = cart_item.quantity
    else:
        cart = request.session.get('cart', {})
        if str(product.slug) in cart:
            cart_quantity = cart[str(product.slug)].get('quantity', 0)
    approved_reviews = product.reviews.filter(is_approved=True, parent__isnull=True).prefetch_related(
        'replies', 'replies__replies', 'replies__replies__replies', 'replies__replies__replies__replies'
    )
    avg_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    context = {
        'product': product,
        'cart_quantity': cart_quantity,
        'approved_reviews': approved_reviews,
        'avg_rating': round(avg_rating, 1),
        'approved_reviews_count': approved_reviews.count(),
    }
    return render(request, 'fd.html', context)

def prpo (request):
    return render(request, 'ecommerce/prpo.html')

def tms (request):
    return render(request, 'ecommerce/tms.html')

def coming_soon (request):
    return render(request, 'ecommerce/coming_soon.html')


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

