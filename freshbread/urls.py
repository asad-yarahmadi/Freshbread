from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin_adminali_admin/', admin.site.urls),

    # 🌐 Public / Ecommerce
    path('', include('core.interfaces.http.urls.ecommerce_urls')),

    # 🔐 Auth
    path('auth/', include('core.interfaces.http.urls.auth_urls')),

    # 👤 Profile
    path('profile/', include('core.interfaces.http.urls.profile_urls')),

    # 📦 Orders
    path('orders/', include('core.interfaces.http.urls.order_urls')),

    # ⭐ Reviews
    path('reviews/', include('core.interfaces.http.urls.review_urls')),

    # ⭐ Reviews
    path('blog/', include('core.interfaces.http.urls.blog_urls')),

    # ⭐ Reviews
    path('cart/', include('core.interfaces.http.urls.cart_urls')),

    # ⭐ Reviews
    path('product/', include('core.interfaces.http.urls.products_urls')),

    # ⭐ Reviews
    path('checkout/', include('core.interfaces.http.urls.checkout_urls')),

    # 🧾 Tickets
    path('tickets/', include('core.interfaces.http.urls.ticket_urls')),
    # 🛠 Admin Tools
    path('admin_tools/', include('core.interfaces.http.urls.admin_urls')),
]

handler404 = 'core.interfaces.http.views.errors_view.handler404'
handler403 = 'core.interfaces.http.views.errors_view.handler403'
handler500 = 'core.interfaces.http.views.errors_view.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])