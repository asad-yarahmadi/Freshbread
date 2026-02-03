"""
Adapter برای تبدیل درخواست‌های HTTP به DTO برای Product Management
"""
from django.http import HttpRequest
from decimal import Decimal
from typing import Dict, Any, Optional, List

from core.application.dto.product_dto import CreateProductDTO, UpdateProductDTO


def extract_product_form_data(request: HttpRequest) -> Dict[str, Any]:
    """
    استخراج داده‌های فرم محصول از request
    
    Args:
        request: Django HttpRequest
    
    Returns:
        Dict[str, Any]: داده‌های محصول
    """
    return {
        'name': request.POST.get('name', '').strip(),
        'slug': request.POST.get('slug', '').strip(),
        'description': request.POST.get('description', '').strip(),
        'price': Decimal(request.POST.get('price', '0')) if request.POST.get('price') else Decimal('0'),
        'original_price': Decimal(request.POST.get('original_price', '')) if request.POST.get('original_price') else None,
        'category': request.POST.get('category', '').strip(),
        'available': request.POST.get('available') == 'on',
    }


def create_create_product_dto(form_data: Dict[str, Any], images: List = None) -> CreateProductDTO:
    """
    ایجاد DTO برای ایجاد محصول
    
    Args:
        form_data: داده‌های فرم
        images: لیست فایل‌های عکس
    
    Returns:
        CreateProductDTO
    """
    return CreateProductDTO(
        name=form_data['name'],
        slug=form_data['slug'],
        description=form_data.get('description'),
        price=form_data['price'],
        original_price=form_data.get('original_price'),
        category=form_data.get('category'),
        available=form_data.get('available', True),
        images=images
    )


def create_update_product_dto(product_id: int, form_data: Dict[str, Any]) -> UpdateProductDTO:
    """
    ایجاد DTO برای بروزرسانی محصول
    
    Args:
        product_id: شناسهٔ محصول
        form_data: داده‌های فرم
    
    Returns:
        UpdateProductDTO
    """
    return UpdateProductDTO(
        product_id=product_id,
        name=form_data.get('name'),
        slug=form_data.get('slug'),
        description=form_data.get('description'),
        price=form_data.get('price'),
        original_price=form_data.get('original_price'),
        category=form_data.get('category'),
        available=form_data.get('available')
    )


def convert_dto_to_dict(dto: UpdateProductDTO) -> Dict[str, Any]:
    """
    تبدیل UpdateProductDTO به dictionary (فقط فیلدهای پر‌شده)
    
    Args:
        dto: UpdateProductDTO
    
    Returns:
        Dict[str, Any]
    """
    data = {}
    
    if dto.name is not None:
        data['name'] = dto.name
    if dto.slug is not None:
        data['slug'] = dto.slug
    if dto.description is not None:
        data['description'] = dto.description
    if dto.price is not None:
        data['price'] = dto.price
    if dto.original_price is not None:
        data['original_price'] = dto.original_price
    if dto.category is not None:
        data['category'] = dto.category
    if dto.available is not None:
        data['available'] = dto.available
    
    return data
