"""
Domain utility: تولید کد تایید
"""
import random
import string


def generate_verification_code(length: int = 6) -> str:
    """
    تولید یک کد تایید تصادفی
    
    Args:
        length: طول کد (پیش‌فرض: 6 کاراکتر)
    
    Returns:
        str: کد تایید شامل حروف و اعداد
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
