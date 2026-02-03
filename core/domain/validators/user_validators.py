import re
from django.core.exceptions import ValidationError

def validate_username(value):
    if not value:
        raise ValidationError("Username cannot be empty.")
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise ValidationError("Username may only contain English letters, digits, and underscores (_).")
    if " " in value:
        raise ValidationError("Username cannot contain spaces.")
    if "@" in value:
        raise ValidationError("Username cannot contain '@'.")
    if re.search(r'[\u0600-\u06FF]', value):
        raise ValidationError("Username cannot contain Persian or Arabic characters.")
    if not (4 <= len(value) <= 30):
        raise ValidationError("Username must be between 4 and 30 characters long.")
