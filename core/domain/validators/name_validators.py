import regex
from django.core.exceptions import ValidationError

def validate_name(value):
    if not value:
        raise ValidationError("This field cannot be empty.")
    if not regex.match(r'^[\p{L}\p{M}\s-]+$', value):
        raise ValidationError("Name may only contain letters, spaces, or hyphens.")
    if regex.search(r'\p{N}', value):
        raise ValidationError("Name cannot contain numbers.")
    if regex.search(r'(.)\1{2,}', value):
        raise ValidationError("Name cannot contain excessive repetition of the same character.")
    if len(set(value)) == 1:
        raise ValidationError("Name cannot consist of only one repeated character.")
    if not (2 <= len(value) <= 30):
        raise ValidationError("Name must be between 2 and 30 characters long.")
