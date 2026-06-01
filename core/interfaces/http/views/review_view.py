from django.shortcuts import render, redirect, get_object_or_404
from ..decorators import admin_login_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.infrastructure.models import BlogReview, Review
from core.infrastructure.email.email_sender import email_sender
from django.urls import reverse
@admin_login_protect
def review_check(request):
    from core.application.services.review_service import ReviewService
    reviews = ReviewService.get_all_reviews()
    blog_reviews = BlogReview.objects.all().order_by('-created_at')
    return render(request, 'freshbread/review/review_check.html', {'reviews': reviews, 'blog_reviews': blog_reviews})

@admin_login_protect
def approve_review(request, review_id):
    from core.application.services.review_service import ReviewService
    if request.method == 'POST':
        try:
            # approve
            res = ReviewService.approve_review(review_id)
            # notify parent if this is a reply
            try:
                rv = Review.objects.select_related('parent', 'product').get(id=review_id)
                if rv.parent and (rv.parent.email or (rv.parent.user and rv.parent.user.email)):
                    parent_email = rv.parent.email or (rv.parent.user.email if rv.parent.user else None)
                    if parent_email:
                        path = reverse('food_de', args=[rv.product.slug])
                        action_url = f"https://kingfood.ca{path}"
                        html = f"<p>Someone replied to your comment on <strong>{rv.product.name}</strong>.</p><blockquote>{rv.comment}</blockquote>"
                        email_sender.send(
                            subject="New reply to your comment",
                            message=f"New reply on {rv.product.name}: {rv.comment}",
                            html_message=html,
                            to=parent_email,
                            title="New Reply",
                            cta_text="Open Product",
                            action_url=action_url,
                            wrap=True,
                        )
            except Exception:
                pass
            messages.success(request, "✅ Review approved.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('review_check')

@admin_login_protect
def delete_review(request, review_id):
    from core.application.services.review_service import ReviewService
    try:
        ReviewService.delete_review(review_id, request.user)
        messages.success(request, "✔ Review deleted.")
    except Exception as e:
        messages.error(request, str(e))
    return redirect('review_check')

@admin_login_protect
def approve_blog_review(request, review_id):
    if request.method == 'POST':
        try:
            br = BlogReview.objects.select_related('parent', 'post').get(id=review_id)
            br.is_approved = True
            br.save(update_fields=['is_approved'])
            # notify parent if this is a reply
            try:
                if br.parent and (br.parent.email or (br.parent.user and br.parent.user.email)):
                    parent_email = br.parent.email or (br.parent.user.email if br.parent.user else None)
                    if parent_email:
                        path = reverse('blog_details', args=[br.post.slug])
                        action_url = f"https://kingfood.ca{path}"
                        html = f"<p>Someone replied to your comment on blog post <strong>{br.post.title}</strong>.</p><blockquote>{br.comment}</blockquote>"
                        email_sender.send(
                            subject="New reply to your comment",
                            message=f"New reply on {br.post.title}: {br.comment}",
                            html_message=html,
                            to=parent_email,
                            title="New Reply",
                            cta_text="Open Post",
                            action_url=action_url,
                            wrap=True,
                        )
            except Exception:
                pass
            messages.success(request, "✅ Blog review approved.")
        except BlogReview.DoesNotExist:
            messages.error(request, "Blog review not found.")
    return redirect('review_check')

@admin_login_protect
def delete_blog_review(request, review_id):
    try:
        br = BlogReview.objects.get(id=review_id)
        br.delete()
        messages.success(request, "✔ Blog review deleted.")
    except BlogReview.DoesNotExist:
        messages.error(request, "Blog review not found.")
    return redirect('review_check')

@admin_login_protect
def ban_user_from_blog_review(request, review_id):
    if request.method == 'POST':
        try:
            br = BlogReview.objects.get(id=review_id)
            if br.user:
                br.user.is_active = False
                br.user.save(update_fields=['is_active'])
                messages.warning(request, "🚫 User banned from submitting blog reviews.")
            else:
                messages.error(request, "This blog review was submitted by a guest user.")
        except BlogReview.DoesNotExist:
            messages.error(request, "Blog review not found.")
    return redirect('review_check')

@admin_login_protect
def ban_user_from_review(request, review_id):
    from core.application.services.review_service import ReviewService
    if request.method == 'POST':
        try:
            ReviewService.ban_user_from_reviews(review_id)
            messages.warning(request, "🚫 User banned.")
        except Exception as e:
            messages.error(request, str(e))
    return redirect('review_check')

def add_review(request, slug):
    from core.interfaces.forms.auth_forms import ReviewForm
    from core.application.services.review_service import ReviewService
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        images = request.FILES.getlist('images')
        if form.is_valid():
            data = form.cleaned_data
            try:
                ReviewService.create_review(slug, data, images, request.user)
                messages.success(request, "✅ Your review was submitted and will appear after admin approval.")
                return redirect('food_de', slug=slug)
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ReviewForm()
    from core.infrastructure.repositories.product_repository import ProductRepository
    product = ProductRepository.get_product_by_slug(slug)
    return render(request, 'freshbread/fd.html', {'review_form': form, 'product': product})


@login_required
def reply_review(request, review_id):
    parent = get_object_or_404(Review.objects.select_related('product'), id=review_id)
    if request.method != 'POST':
        return redirect('food_de', slug=parent.product.slug)
    comment = (request.POST.get('comment') or '').strip()
    if not comment:
        messages.error(request, "Reply cannot be empty.")
        return redirect('food_de', slug=parent.product.slug)
    if getattr(parent, 'depth', 1) >= 6:
        messages.error(request, "Reply chain is full for this comment.")
        return redirect('food_de', slug=parent.product.slug)
    rv = Review.objects.create(
        product=parent.product,
        parent=parent,
        depth=(getattr(parent, 'depth', 1) + 1),
        user=request.user,
        first_name=request.user.first_name or request.user.username,
        last_name=request.user.last_name or "",
        email=request.user.email,
        rating=parent.rating,
        comment=comment,
        is_approved=False,
    )
    messages.success(request, "Your reply was submitted and will appear after approval.")
    return redirect('food_de', slug=parent.product.slug)
