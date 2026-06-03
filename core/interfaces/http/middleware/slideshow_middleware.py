from django.utils import timezone
from core.infrastructure.models import SlideshowMode


class SlideshowExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check for active slideshows that have expired
        active_slideshows = SlideshowMode.objects.filter(is_active=True, expires_at__isnull=False)
        for slideshow in active_slideshows:
            if slideshow.is_expired():
                slideshow.is_active = False
                slideshow.save()

        response = self.get_response(request)
        return response
