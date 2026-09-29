from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.infrastructure.sitemaps import StaticViewSitemap, ProductSitemap, BlogPostSitemap

# Define sitemaps dictionary
sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'blog': BlogPostSitemap,
}

urlpatterns = [
    path('admin_adminali_admin/', admin.site.urls),
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # 🌐 Public / Ecommerce
    path('', include('core.interfaces.http.urls.ecommerce_urls')),

    # 🔐 Auth
    path('auth/', include('core.interfaces.http.urls.auth.auth_urls')),

    # 👤 Profile
    path('profile/', include('core.interfaces.http.urls.profile.profile_urls')),

    # 📦 Orders
    path('orders/', include('core.interfaces.http.urls.order.order_urls')),

    # ⭐ Reviews
    path('reviews/', include('core.interfaces.http.urls.ecommerce.review_urls')),

    # ⭐ Reviews
    path('blog/', include('core.interfaces.http.urls.ecommerce.blog_urls')),

    # ⭐ Reviews
    path('cart/', include('core.interfaces.http.urls.order.cart_urls')),

    # ⭐ Reviews
    path('product/', include('core.interfaces.http.urls.admin.products_urls')),

    # ⭐ Reviews
    path('checkout/', include('core.interfaces.http.urls.order.checkout_urls')),

    # 🧾 Tickets
    path('tickets/', include('core.interfaces.http.urls.profile.ticket_urls')),
    
    # 🛠 Admin Tools
    path('admin_tools/', include('core.interfaces.http.urls.admin.admin_urls')),
    
    # 🖼️ Slideshow
    path('slideshow/', include('core.interfaces.http.urls.admin.slideshow_urls')),

    # Badges
    path('badges/', include('core.interfaces.http.urls.profile.badge_urls')),

    # Loations
    path('profile/locations/', include('core.interfaces.http.urls.profile.location_urls')),

    # Admin order
    path('order/review/', include('core.interfaces.http.urls.admin.admin_order_approval_urls')),
    path('order/management/', include('core.interfaces.http.urls.admin.admin_order_managment_urls')),


    
]

handler404 = 'core.interfaces.http.views.ecommerce.errors_view.handler404'
handler403 = 'core.interfaces.http.views.ecommerce.errors_view.handler403'
handler500 = 'core.interfaces.http.views.ecommerce.errors_view.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
