from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Order, DelayedTask, Review, BlogReview, UserBlogView


@receiver(post_save, sender=Order)
def order_status_updated(sender, instance, created, **kwargs):
    if instance.status == 'delivered' and instance.completed_at:
        # Check if we already created a review request
        if not hasattr(instance, 'review_request'):
            from .models import OrderReviewRequest
            OrderReviewRequest.objects.create(order=instance)
        # Create a delayed task to send email after 3 hours
        if not DelayedTask.objects.filter(
            task_type='send_review_email',
            content_type=ContentType.objects.get_for_model(Order),
            object_id=str(instance.id),
            is_processed=False
        ).exists():
            DelayedTask.objects.create(
                task_type='send_review_email',
                content_type=ContentType.objects.get_for_model(Order),
                object_id=str(instance.id),
                scheduled_at=timezone.now() + timezone.timedelta(hours=3)
            )
        # Update badges for food category
        if instance.user:
            from core.application.services.badge_service import update_user_badges
            update_user_badges(instance.user)


@receiver(post_save, sender=Review)
def review_updated(sender, instance, created, **kwargs):
    if instance.user and instance.is_approved:
        from core.application.services.badge_service import update_user_badges
        update_user_badges(instance.user)


@receiver(post_save, sender=BlogReview)
def blog_review_updated(sender, instance, created, **kwargs):
    if instance.user and instance.is_approved:
        from core.application.services.badge_service import update_user_badges
        update_user_badges(instance.user)


@receiver(post_save, sender=UserBlogView)
def blog_view_updated(sender, instance, created, **kwargs):
    if instance.user and instance.is_valid_view:
        from core.application.services.badge_service import update_user_badges
        update_user_badges(instance.user)
