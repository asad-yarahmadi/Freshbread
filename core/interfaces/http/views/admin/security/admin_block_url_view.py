# apps/admin_panel/url_collector.py
from collections import Counter

from django.urls import get_resolver, URLPattern, URLResolver, reverse
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils.text import slugify
from core.infrastructure.models import BlockedURL, BlockLog


PROTECTED_PREFIXES = ("/admin_tools/", "/admin_adminali_admin/")
TAB_CHOICES = {"urls", "blocked", "logs"}


def normalize_url_path(path):
    path = (path or "").strip()
    if not path:
        return "/"

    path = path.replace("^", "").replace("$", "")
    path = "/" + path.strip("/")
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


def categorize_url(path):
    path = normalize_url_path(path)
    if path == "/":
        return "Home"

    first_segment = path.strip("/").split("/", 1)[0]
    category_map = {
        "admin_tools": "Admin Tools",
        "admin_adminali_admin": "Django Admin",
        "auth": "Authentication",
        "profile": "Profiles",
        "orders": "Orders",
        "reviews": "Reviews",
        "blog": "Blog",
        "cart": "Cart",
        "product": "Products",
        "checkout": "Checkout",
        "tickets": "Tickets",
        "static": "Static",
        "media": "Media",
    }
    return category_map.get(first_segment, first_segment.replace("-", " ").replace("_", " ").title())


def redirect_manage_urls(tab):
    safe_tab = tab if tab in TAB_CHOICES else "urls"
    return redirect(f"{reverse('manage_urls')}?tab={safe_tab}")

def get_all_urls(urlpatterns, prefix='', result=None):
    if result is None:
        result = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            full_path = normalize_url_path(prefix + str(pattern.pattern))
            result.append(full_path)
        elif isinstance(pattern, URLResolver):
            get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern), result)
    return result

def get_all_project_urls():
    resolver = get_resolver()
    urls = get_all_urls(resolver.url_patterns)
    return sorted(set(urls))

# apps/admin_panel/views.py


@staff_member_required
def manage_urls(request):
    all_url_paths = get_all_project_urls()
    active_tab = request.GET.get('tab', 'urls')
    if active_tab not in TAB_CHOICES:
        active_tab = 'urls'

    blocked_urls = {
        normalize_url_path(blocked.path): blocked
        for blocked in BlockedURL.objects.filter(is_active=True)
    }

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        path = normalize_url_path(request.POST.get('path'))
        reason = (request.POST.get('reason') or '').strip()
        active_tab = request.POST.get('tab', active_tab)
        if active_tab not in TAB_CHOICES:
            active_tab = 'urls'

        if path not in all_url_paths:
            messages.error(request, 'Selected URL was not found.')
            return redirect_manage_urls(active_tab)

        if any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            messages.error(request, 'This admin URL is protected and cannot be blocked.')
            return redirect_manage_urls(active_tab)

        if action == 'block':
            if not reason:
                messages.error(request, f'Please provide a reason for blocking {path}.')
                return redirect_manage_urls(active_tab)

            blocked, _ = BlockedURL.objects.get_or_create(path=path)
            blocked.reason = reason
            blocked.blocked_by = request.user
            blocked.is_active = True
            blocked.save()

            BlockLog.objects.create(
                blocked_url=blocked,
                action='block',
                changed_by=request.user
            )
            messages.success(request, f'{path} has been blocked.')
            return redirect_manage_urls(active_tab)

        if action == 'unblock':
            blocked = BlockedURL.objects.filter(path=path, is_active=True).first()
            if blocked:
                blocked.is_active = False
                blocked.save()

                BlockLog.objects.create(
                    blocked_url=blocked,
                    action='unblock',
                    changed_by=request.user
                )
                messages.success(request, f'{path} has been unblocked.')
            else:
                messages.error(request, f'No active block was found for {path}.')
            return redirect_manage_urls(active_tab)

        messages.error(request, 'Invalid action.')
        return redirect_manage_urls(active_tab)

    urls_with_status = []
    for path in all_url_paths:
        blocked = blocked_urls.get(path)
        urls_with_status.append({
            'path': path,
            'category': categorize_url(path),
            'category_anchor': f"category-{slugify(categorize_url(path))}",
            'is_blocked': bool(blocked),
            'reason': blocked.reason if blocked else '',
            'is_protected': any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES),
        })

    urls_with_status.sort(key=lambda item: (item['category'].lower(), item['path']))

    visible_urls = urls_with_status
    if active_tab == 'blocked':
        visible_urls = [item for item in urls_with_status if item['is_blocked']]

    category_counts = Counter(item['category'] for item in urls_with_status)
    category_summary = [
        {'name': name, 'count': count, 'anchor': f"category-{slugify(name)}"}
        for name, count in sorted(category_counts.items(), key=lambda item: (item[0].lower(), item[1]))
    ]

    logs = BlockLog.objects.select_related('blocked_url', 'changed_by').order_by('-changed_at')[:50]
    logs_data = [{
        'url': log.blocked_url.path,
        'action': log.action,
        'reason': log.blocked_url.reason if log.action == 'block' else '',
        'admin': log.changed_by.username if log.changed_by else 'system',
        'timestamp': log.changed_at,
    } for log in logs]
    
    blocked_count = sum(1 for item in urls_with_status if item['is_blocked'])
    active_count = len(all_url_paths) - blocked_count

    return render(request, 'freshbread/admin/block_url.html', {
        'urls': visible_urls,
        'logs': logs_data,
        'category_summary': category_summary,
        'blocked_count': blocked_count,
        'active_count': active_count,
        'active_tab': active_tab,
        'total_url_count': len(all_url_paths),
    })

@staff_member_required
def log_list(request):
    return redirect(f"{reverse('manage_urls')}?tab=logs")
