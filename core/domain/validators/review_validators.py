"""
Domain Layer: Review Validators
اعتبارسنجی‌های نظرات
"""
from typing import Dict, Any, List
import re


def validate_review_rating(rating: int) -> None:
    """
    اعتبارسنجی امتیاز نظر
    
    Args:
        rating: امتیاز
    
    Raises:
        ValueError: اگر امتیاز نامعتبر باشد
    """
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        raise ValueError("Rating must be an integer between 1 and 5")


def validate_review_text(text: str, field_name: str, max_length: int = 1000) -> None:
    """
    اعتبارسنجی متن نظر
    
    Args:
        text: متن
        field_name: نام فیلد
        max_length: حداکثر طول
    
    Raises:
        ValueError: اگر متن نامعتبر باشد
    """
    if not text or not text.strip():
        raise ValueError(f"{field_name} cannot be empty")
    
    if len(text.strip()) > max_length:
        raise ValueError(f"{field_name} cannot exceed {max_length} characters")


def validate_review_name(name: str, field_name: str) -> None:
    """
    اعتبارسنجی نام
    
    Args:
        name: نام
        field_name: نام فیلد
    
    Raises:
        ValueError: اگر نام نامعتبر باشد
    """
    if not name or not name.strip():
        raise ValueError(f"{field_name} cannot be empty")
    
    if len(name.strip()) < 2:
        raise ValueError(f"{field_name} must be at least 2 characters")
    
    if len(name.strip()) > 50:
        raise ValueError(f"{field_name} cannot exceed 50 characters")
    
    # بررسی کاراکترهای غیرمجاز
    if re.search(r'[<>]', name):
        raise ValueError(f"{field_name} contains invalid characters")


def validate_email_format(email: str) -> None:
    """
    اعتبارسنجی فرمت ایمیل
    
    Args:
        email: ایمیل
    
    Raises:
        ValueError: اگر ایمیل نامعتبر باشد
    """
    if not email:
        return  # ایمیل اختیاری است
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")


def validate_review_data(data: Dict[str, Any]) -> None:
    """
    اعتبارسنجی داده‌های نظر
    
    Args:
        data: داده‌های نظر
    
    Raises:
        ValueError: اگر داده‌ها نامعتبر باشند
    """
    required_fields = ['first_name', 'rating', 'comment']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Field {field} is required")
    
    validate_review_name(data['first_name'], 'نام')
    if 'last_name' in data and data['last_name']:
        validate_review_name(data['last_name'], 'نام خانوادگی')
    validate_review_rating(data['rating'])
    validate_review_text(data['comment'], 'نظر', 1000)
    
    if 'email' in data and data['email']:
        validate_email_format(data['email'])


def validate_image_files(images: List[Any], max_count: int = 5) -> None:
    """
    اعتبارسنجی فایل‌های تصویر
    
    Args:
        images: لیست فایل‌ها
        max_count: حداکثر تعداد
    
    Raises:
        ValueError: اگر فایل‌ها نامعتبر باشند
    """
    if len(images) > max_count:
        raise ValueError(f"حداکثر {max_count} تصویر مجاز است")
    
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
    max_size = 5 * 1024 * 1024  # 5MB
    
    for image in images:
        if hasattr(image, 'name'):
            ext = image.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValueError(f"فرمت فایل {ext} پشتیبانی نمی‌شود")
            
            if hasattr(image, 'size') and image.size > max_size:
                raise ValueError("حجم فایل تصویر نمی‌تواند بیش از 5 مگابایت باشد")