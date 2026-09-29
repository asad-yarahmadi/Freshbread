from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def badge_explorer(request):
    from core.infrastructure.models import Badge, UserBadge, BadgeCategory
    from core.application.services.badge_service import get_user_badge_progress, initialize_badges

    initialize_badges()
    
    categories = BadgeCategory.objects.filter(is_public=True).order_by('sort_order', 'name')
    earned_badge_ids = UserBadge.objects.filter(user=request.user).values_list('badge_id', flat=True)
    badge_progress = get_user_badge_progress(request.user)
    
    category_data = []
    for category in categories:
        badges = Badge.objects.filter(category=category, is_active=True).order_by('level')
        badge_list = []
        for badge in badges:
            progress = 0
            cat_key = category.name.lower().replace(' ', '_')
            if cat_key in badge_progress:
                current_count = badge_progress[cat_key].get('current_count', 0)
                if badge.progress_target > 0:
                    progress = min((current_count / badge.progress_target) * 100, 100)
            
            badge_list.append({
                'badge': badge,
                'type': 'earned' if badge.id in earned_badge_ids else 'locked',
                'progress': progress
            })
        
        category_data.append({
            'category': category,
            'badges': badge_list
        })
    
    total_badges = Badge.objects.filter(is_active=True).count()
    total_earned = len(earned_badge_ids)
    
    return render(
        request,
        "freshbread/profile/badge_explorer.html",
        {
            "categories": category_data,
            "total_badges": total_badges,
            "total_earned": total_earned
        }
    )
