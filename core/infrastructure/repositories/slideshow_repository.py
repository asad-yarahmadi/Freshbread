from typing import Optional, List
from django.utils import timezone
from core.infrastructure.models import SlideshowMode, Slide, SlideButton


class SlideshowRepository:
    @staticmethod
    def get_active_slideshow() -> Optional[SlideshowMode]:
        """
        Get the currently active slideshow mode, checking for expiry first
        """
        # First, check if any active mode is expired
        active_modes = SlideshowMode.objects.filter(is_active=True)
        for mode in active_modes:
            if mode.is_expired():
                mode.is_active = False
                mode.save()
        
        # Now get the non-expired active mode
        active = SlideshowMode.objects.filter(is_active=True).first()
        
        # If no active, use default
        if not active:
            active = SlideshowMode.objects.filter(is_default=True).first()
        
        # If still no mode, try to create default
        if not active:
            return SlideshowRepository.create_default_slideshow()
        
        return active

    @staticmethod
    def create_default_slideshow() -> SlideshowMode:
        """
        Create the default slideshow mode with 3 slides
        """
        from django.conf import settings
        import os

        default_mode, created = SlideshowMode.objects.get_or_create(
            name="Default Slideshow",
            defaults={
                'is_default': True,
                'is_active': True
            }
        )

        # If we just created it, add default slides
        if created:
            # Slide 1
            slide1 = Slide.objects.create(
                slideshow_mode=default_mode,
                title="Welcome To Kingfood",
                description="Enjoy handmade bread, cakes, foods and pastries from your local bakery in Ottawa. Reserve a table or order freshly baked treats today.",
                text_position='center',
                sort_order=0
            )
            SlideButton.objects.create(
                slide=slide1,
                text="reservation",
                url="/menu/",
                sort_order=0
            )

            # Slide 2
            slide2 = Slide.objects.create(
                slideshow_mode=default_mode,
                description="King Food, based in Ottawa, specializes in producing and serving high-quality Persian dishes, fast food, bread, cakes, pastries, desserts, and appetizers.",
                text_position='center',
                sort_order=1
            )
            SlideButton.objects.create(
                slide=slide2,
                text="Buy!",
                url="/reservation/",
                sort_order=0
            )

            # Slide 3
            slide3 = Slide.objects.create(
                slideshow_mode=default_mode,
                description="Our mission is to provide fresh, delicious, and diverse food products while delivering an exceptional dining experience to our customers.",
                text_position='center',
                sort_order=2
            )
            SlideButton.objects.create(
                slide=slide3,
                text="Menu",
                url="/menu/",
                sort_order=0
            )

        return default_mode

    @staticmethod
    def get_all_modes() -> List[SlideshowMode]:
        return list(SlideshowMode.objects.all())

    @staticmethod
    def get_mode_by_id(mode_id: int) -> Optional[SlideshowMode]:
        try:
            return SlideshowMode.objects.prefetch_related('slides__buttons').get(id=mode_id)
        except SlideshowMode.DoesNotExist:
            return None

    @staticmethod
    def set_active_mode(mode: SlideshowMode) -> None:
        # Deactivate all other modes
        SlideshowMode.objects.exclude(id=mode.id).update(is_active=False)
        mode.is_active = True
        mode.save()
