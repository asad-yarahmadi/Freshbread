from django.core.management.base import BaseCommand
from django.utils import timezone
from core.infrastructure.models import DelayedTask, Order, OrderReviewRequest
from core.infrastructure.email.email_sender import email_sender
from django.urls import reverse

class Command(BaseCommand):
    help = "Process delayed tasks"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        tasks = DelayedTask.objects.filter(scheduled_at__lte=now, is_processed=False)
        
        for task in tasks:
            try:
                if task.task_type == 'send_review_email':
                    order = Order.objects.get(id=task.object_id)
                    review_request, created = OrderReviewRequest.objects.get_or_create(order=order)
                    
                    if not review_request.is_submitted:
                        # Send email
                        review_url = reverse('submit_order_review', args=[review_request.token])
                        full_url = f"https://kingfood.ca{review_url}"
                        
                        email_sender.send(
                            subject="How was your order with Kingfood?",
                            title="We'd love your feedback!",
                            message=f"Hi {order.user.first_name or order.user.username},\n\nWe hope you enjoyed your order! Please leave us a review here:\n{full_url}",
                            to=order.user.email,
                            cta_text="Leave a Review",
                            action_url=full_url
                        )
                        review_request.sent_at = now
                        review_request.save()
                
                # Mark as processed
                task.is_processed = True
                task.processed_at = now
                task.save()
                self.stdout.write(self.style.SUCCESS(f"Processed task {task.id}"))
                
            except Exception as e:
                task.error = str(e)
                task.save()
                self.stdout.write(self.style.ERROR(f"Error processing task {task.id}: {e}"))
