"""
HTTP Adapters
"""
from .password_reset_adapter import (
    extract_password_reset_data,
    extract_verification_data,
    extract_password_reset_complete_data,
    create_password_reset_response
)
from .product_adapter import (
    extract_create_product_data,
    extract_update_product_data,
    create_product_response,
    format_product_for_template
)
from .cart_adapter import (
    extract_add_to_cart_data,
    extract_set_quantity_data,
    create_cart_response,
    format_cart_summary_for_template
)

__all__ = [
    # Password Reset
    'extract_password_reset_data', 'extract_verification_data',
    'extract_password_reset_complete_data', 'create_password_reset_response',

    # Product
    'extract_create_product_data', 'extract_update_product_data',
    'create_product_response', 'format_product_for_template',

    # Cart
    'extract_add_to_cart_data', 'extract_set_quantity_data',
    'create_cart_response', 'format_cart_summary_for_template'
]