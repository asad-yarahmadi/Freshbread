from django.shortcuts import render, redirect
from ..decorators import admin_login_protect
from django.contrib import messages
from core.infrastructure.models import BlogReview
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
            ReviewService.approve_review(review_id)
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
            br = BlogReview.objects.get(id=review_id)
            br.is_approved = True
            br.save(update_fields=['is_approved'])
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
