from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.interfaces.http.views.ecommerce_views import *
from core.interfaces.http.views.release_view import releases_list, release_detail

urlpatterns = [
    # Home & Public Pages
    path('', index, name='index'),
    path('menu/', menu, name='menu'),
    path('food_deatails/<slug:slug>/', food_de, name='food_de'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('gallery/', gallery, name='gallery'),
    path('privacy_policy', prpo, name='prpo'),
    path('terms_of_use', tms, name='tms'),
    path('stuff/', stuff, name='stuff'),
    path('coming/', coming_soon, name='coming_soon'),
    path('releases/', releases_list, name='releases_list'),
    path('releases/<str:version>/', release_detail, name='release_detail'),

    # API
    path('api/reverse-geocode/', reverse_geocode, name='reverse_geocode'),
    path('api/countdown/', get_countdown_data, name='api_countdown'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
