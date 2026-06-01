import re

from django.utils.deprecation import MiddlewareMixin


PROTECTED_PREFIXES = ('/admin_tools/', '/admin_adminali_admin/')


def normalize_request_path(path):
    path = (path or '').strip()
    if not path:
        return '/'

    path = '/' + path.strip('/')
    if path != '/' and not path.endswith('/'):
        path += '/'
    return path


def blocked_pattern_matches(blocked_path, request_path):
    blocked_path = normalize_request_path(blocked_path)
    request_path = normalize_request_path(request_path)

    if blocked_path == request_path:
        return True

    converter_patterns = {
        'int': r'\d+',
        'slug': r'[-a-zA-Z0-9_]+',
        'uuid': r'[0-9a-fA-F-]+',
        'path': r'.+',
        'str': r'[^/]+',
    }

    def replace_converter(match):
        converter = match.group(1) or 'str'
        return f"({converter_patterns.get(converter, r'[^/]+')})"

    pattern = re.sub(r'<(?:(\w+):)?\w+>', replace_converter, blocked_path)
    return re.fullmatch(pattern, request_path) is not None

class URLBlockerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        path = normalize_request_path(request.path_info)

        if any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            return None

        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False) and (user.is_staff or user.is_superuser):
            return None

        from core.infrastructure.models import BlockedURL
        from core.interfaces.http.views.errors_view import handler404

        try:
            blocked = None
            for candidate in BlockedURL.objects.filter(is_active=True).only('path', 'reason'):
                if blocked_pattern_matches(candidate.path, path):
                    blocked = candidate
                    break

            if blocked:
                return handler404(request, None)

        except Exception:
            return None

        return None
