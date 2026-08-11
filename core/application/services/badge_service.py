from django.contrib.auth import get_user_model
from django.db.models import Sum
from core.infrastructure.models import (
    BadgeCategory, Badge, UserBadge, ClaimedBadgeReward, Order, OrderItem, Review, BlogReview, UserBlogView
)


User = get_user_model()


def initialize_badges():
    """
    Creates all the required badges and categories in the database if they don't exist.
    """
    # First, create categories
    categories = [
        ('Food', 'For ordering food'),
        ('Comments', 'For leaving comments'),
        ('Blog Comments', 'For leaving blog comments'),
        ('Blog Reading', 'For reading blogs'),
    ]
    
    category_objects = {}
    for idx, (name, desc) in enumerate(categories):
        cat, _ = BadgeCategory.objects.get_or_create(
            name=name, 
            defaults={
                'description': desc,
                'sort_order': idx,
                'is_public': True
            }
        )
        category_objects[name.lower().replace(' ', '_')] = cat

    # Now create badges
    rarity_map = {1: 'common', 2: 'uncommon', 3: 'rare', 4: 'epic'}
    badges_data = [
        # Food Category
        {'category': 'food', 'level': 1, 'name': 'Food Explorer', 'progress_target': 1, 'description': 'Ordered your first food!', 'reward_text': '', 'color': '#CD7F32'},
        {'category': 'food', 'level': 2, 'name': 'Taste Hunter', 'progress_target': 10, 'description': 'Ordered 10 dishes!', 'reward_text': '', 'color': '#C0C0C0'},
        {'category': 'food', 'level': 3, 'name': 'Gourmet Customer', 'progress_target': 50, 'description': 'Ordered 50 dishes!', 'reward_text': 'If he gets one of these two badges, exclusive discounts of more than 40% will be activated for him. And as a thank you, he will be sent two free dishes of his choice!', 'color': '#FFD700'},
        {'category': 'food', 'level': 4, 'name': 'King Food VIP', 'progress_target': 100, 'description': 'Ordered 100 dishes!', 'reward_text': 'If he gets one of these two badges, exclusive discounts of more than 40% will be activated for him. And as a thank you, he will be sent two free dishes of his choice!', 'color': '#E5E4E2'},

        # Comments Category
        {'category': 'comments', 'level': 1, 'name': 'First Reviewer', 'progress_target': 1, 'description': 'Left your first verified comment!', 'reward_text': '', 'color': '#CD7F32'},
        {'category': 'comments', 'level': 2, 'name': 'Trusted Critic', 'progress_target': 10, 'description': 'Left 10 verified comments!', 'reward_text': '', 'color': '#C0C0C0'},
        {'category': 'comments', 'level': 3, 'name': 'Food Expert', 'progress_target': 50, 'description': 'Left 50 verified comments!', 'reward_text': 'If these two are activated, because this user has had useful comments and has been verified, they will receive the Pro tag next to their name and will appear wherever they leave a comment. In addition, they will be sent a free dessert with their next order.', 'color': '#FFD700'},
        {'category': 'comments', 'level': 4, 'name': 'Master Reviewer', 'progress_target': 100, 'description': 'Left 100 verified comments!', 'reward_text': 'If these two are activated, because this user has had useful comments and has been verified, they will receive the Pro tag next to their name and will appear wherever they leave a comment. In addition, they will be sent a free dessert with their next order.', 'color': '#E5E4E2'},

        # Blog Comments Category
        {'category': 'blog_comments', 'level': 1, 'name': 'Blog Commenter', 'progress_target': 1, 'description': 'Left your first verified blog comment!', 'reward_text': '', 'color': '#CD7F32'},
        {'category': 'blog_comments', 'level': 2, 'name': 'Active Contributor', 'progress_target': 10, 'description': 'Left 10 verified blog comments!', 'reward_text': '', 'color': '#C0C0C0'},
        {'category': 'blog_comments', 'level': 3, 'name': 'Community Voice', 'progress_target': 50, 'description': 'Left 50 approved blog comments!', 'reward_text': 'This user has become one of the most active members of the King Food community. If they receive one of these two badges, the Community Voice badge will be displayed on their public profile and they will receive a free drink with their next order.', 'color': '#FFD700'},
        {'category': 'blog_comments', 'level': 4, 'name': 'Blog Legend', 'progress_target': 100, 'description': 'Left 100 approved blog comments!', 'reward_text': 'This user has become one of the most active members of the King Food community. If they receive one of these two badges, the Community Voice badge will be displayed on their public profile and they will receive a free drink with their next order.', 'color': '#E5E4E2'},

        # Blog Reading Category
        {'category': 'blog_reading', 'level': 1, 'name': 'Curious Reader', 'progress_target': 10, 'description': 'Viewed 10 blog articles!', 'reward_text': '', 'color': '#CD7F32'},
        {'category': 'blog_reading', 'level': 2, 'name': 'Knowledge Seeker', 'progress_target': 50, 'description': 'Viewed 50 blog articles!', 'reward_text': '', 'color': '#C0C0C0'},
        {'category': 'blog_reading', 'level': 3, 'name': 'Blog Enthusiast', 'progress_target': 100, 'description': 'Viewed 100 blog articles!', 'reward_text': 'This user is very interested in learning and reading educational content. If they receive one of these two badges, they will have access to special content, exclusive training, and selected articles from King Food.', 'color': '#FFD700'},
        {'category': 'blog_reading', 'level': 4, 'name': 'Food Scholar', 'progress_target': 250, 'description': 'Viewed 250 blog articles!', 'reward_text': 'This user is very interested in learning and reading educational content. If they receive one of these two badges, they will have access to special content, exclusive training, and selected articles from King Food.', 'color': '#E5E4E2'},
    ]

    for data in badges_data:
        if data['category'] in category_objects:
            Badge.objects.get_or_create(
                category=category_objects[data['category']],
                level=data['level'],
                defaults={
                    'name': data['name'],
                    'progress_target': data['progress_target'],
                    'description': data['description'],
                    'requirement': data['description'],
                    'reward_text': data['reward_text'],
                    'rarity': rarity_map.get(data['level'], 'common'),
                    'color': data.get('color', '#000000'),
                    'is_public': True,
                    'is_active': True,
                    'sort_order': data['level']
                }
            )


def get_user_food_count(user):
    """
    Calculates the total number of dishes (items) the user has ordered (only delivered orders).
    """
    return OrderItem.objects.filter(
        order__user=user,
        order__status='delivered'
    ).aggregate(total=Sum('quantity'))['total'] or 0


def get_user_comments_count(user):
    """
    Calculates the number of verified (approved) reviews the user has left.
    """
    return Review.objects.filter(
        user=user,
        is_approved=True
    ).count()


def get_user_blog_comments_count(user):
    """
    Calculates the number of approved blog reviews the user has left.
    """
    return BlogReview.objects.filter(
        user=user,
        is_approved=True
    ).count()


def get_user_blog_views_count(user):
    """
    Calculates the number of unique blog articles the user has viewed (only valid views).
    """
    return UserBlogView.objects.filter(user=user, is_valid_view=True).count()


def update_user_badges(user):
    """
    Checks all badge categories for the user and awards any new badges they qualify for.
    """
    initialize_badges()
    new_badges = []

    # Get all categories
    categories = BadgeCategory.objects.all()
    
    for category in categories:
        # Determine count based on category
        category_name = category.name.lower().replace(' ', '_')
        if category_name == 'food':
            current_count = get_user_food_count(user)
        elif category_name == 'comments':
            current_count = get_user_comments_count(user)
        elif category_name == 'blog_comments':
            current_count = get_user_blog_comments_count(user)
        elif category_name == 'blog_reading':
            current_count = get_user_blog_views_count(user)
        else:
            continue
            
        # Get badges for this category
        badges = Badge.objects.filter(category=category).order_by('level')
        
        for badge in badges:
            if current_count >= badge.progress_target:
                obj, created = UserBadge.objects.get_or_create(user=user, badge=badge)
                if created:
                    new_badges.append(obj)

    # Send emails for new badges
    for user_badge in new_badges:
        send_badge_congratulatory_email(user_badge)

    return new_badges


def send_badge_congratulatory_email(user_badge):
    """
    Sends a congratulatory email when a user earns a badge.
    """
    if user_badge.congratulatory_email_sent:
        return

    from django.core.mail import send_mail
    from django.conf import settings

    subject = f"Congratulations! You earned the {user_badge.badge.name} badge!"
    message = f"Dear {user_badge.user.username},\n\nCongratulations! You have earned the {user_badge.badge.name} badge!\n"
    if user_badge.badge.reward_text:
        message += f"\n{user_badge.badge.reward_text}\nYou can claim your reward in your next order!"

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user_badge.user.email],
            fail_silently=False,
        )
        user_badge.congratulatory_email_sent = True
        user_badge.save()
    except Exception as e:
        print(f"Error sending email: {e}")


def get_available_rewards(user):
    """
    Returns the list of badges with rewards that the user has earned but not yet claimed.
    """
    # Get all earned badges with rewards
    earned_badges = UserBadge.objects.filter(
        user=user,
        badge__reward_text__isnull=False
    ).exclude(badge__reward_text='').select_related('badge')

    # Get claimed badges
    claimed_badge_ids = ClaimedBadgeReward.objects.filter(
        user=user
    ).values_list('badge__id', flat=True)

    # Filter to get only unclaimed rewards
    available_rewards = []
    for user_badge in earned_badges:
        if user_badge.badge.id not in claimed_badge_ids:
            available_rewards.append(user_badge.badge)

    return available_rewards


def claim_reward(user, badge, order):
    """
    Marks a badge reward as claimed for a specific order.
    """
    return ClaimedBadgeReward.objects.get_or_create(
        user=user,
        badge=badge,
        defaults={'order': order}
    )


def get_user_badge_progress(user):
    """
    Returns a dictionary with badge progress for each category, including current count,
    next badge, and percentage completed.
    """
    initialize_badges()

    progress = {}
    categories = BadgeCategory.objects.all()
    
    for category in categories:
        category_name = category.name.lower().replace(' ', '_')
        # Determine count based on category
        if category_name == 'food':
            current_count = get_user_food_count(user)
        elif category_name == 'comments':
            current_count = get_user_comments_count(user)
        elif category_name == 'blog_comments':
            current_count = get_user_blog_comments_count(user)
        elif category_name == 'blog_reading':
            current_count = get_user_blog_views_count(user)
        else:
            current_count = 0
            
        # Get badges for this category
        badges = Badge.objects.filter(category=category).order_by('level')
        progress[category_name] = calculate_category_progress(user, current_count, badges)

    return progress


def calculate_category_progress(user, current_count, badges):
    """
    Helper function to calculate progress for a specific category.
    """
    earned_badges = UserBadge.objects.filter(
        user=user,
        badge__in=badges
    ).values_list('badge__id', flat=True)

    badge_list = []
    next_badge = None
    max_level = 0

    for badge in badges:
        is_earned = badge.id in earned_badges
        if is_earned:
            max_level = badge.level

        percentage = 0
        if current_count >= badge.progress_target:
            percentage = 100
        elif badge.progress_target > 0:
            percentage = (current_count / badge.progress_target) * 100

        badge_list.append({
            'badge': badge,
            'is_earned': is_earned,
            'percentage': min(percentage, 100),
        })

        if not is_earned and next_badge is None:
            next_badge = badge

    return {
        'current_count': current_count,
        'badges': badge_list,
        'next_badge': next_badge,
        'max_level': max_level,
    }
