from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class ImageOptimizationError(Exception):
    """Raised when an uploaded image cannot be optimized."""
    pass


class ImageOptimizer:
    """
    Optimize uploaded images before they are stored.

    - Corrects EXIF orientation
    - Limits maximum dimensions
    - Converts JPEG/PNG/etc. to WebP
    - Preserves transparency when present
    """

    MAX_WIDTH = 1600
    MAX_HEIGHT = 1600

    WEBP_QUALITY = 82
    WEBP_METHOD = 6

    @classmethod
    def optimize(cls, uploaded_file):
        if not uploaded_file:
            return None

        try:
            uploaded_file.seek(0)

            image = Image.open(uploaded_file)

            # Correct camera/EXIF orientation.
            image = ImageOps.exif_transpose(image)

            # Force image data to be loaded before the uploaded
            # file is closed/reused.
            image.load()

        except (UnidentifiedImageError, OSError, ValueError) as exc:
            logger.exception("Invalid image uploaded.")
            raise ImageOptimizationError(
                "The uploaded file is not a valid image."
            ) from exc

        # Preserve transparency where it exists.
        has_alpha = (
            image.mode in ("RGBA", "LA")
            or (
                image.mode == "P"
                and "transparency" in image.info
            )
        )

        if has_alpha:
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")

        # Resize only when necessary.
        image.thumbnail(
            (cls.MAX_WIDTH, cls.MAX_HEIGHT),
            Image.Resampling.LANCZOS,
        )

        output = BytesIO()

        image.save(
            output,
            format="WEBP",
            quality=cls.WEBP_QUALITY,
            method=cls.WEBP_METHOD,
            lossless=False,
        )

        output.seek(0)

        original_name = Path(uploaded_file.name).stem
        optimized_name = f"{original_name}.webp"

        return ContentFile(
            output.read(),
            name=optimized_name,
        )