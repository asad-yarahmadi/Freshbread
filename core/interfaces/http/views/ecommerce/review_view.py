from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.infrastructure.models import BlogReview, Review, OrderReviewRequest, Order
from core.infrastructure.email.email_sender import email_sender
from django.urls import reverse

@login_required
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

@login_required
def submit_order_review(request, token):
    from core.interfaces.forms.auth_forms import ReviewForm
    from core.application.services.review_service import ReviewService
    review_request = get_object_or_404(OrderReviewRequest, token=token)
    order = review_request.order
    
    if review_request.is_submitted:
        # If already submitted, redirect to the first product with a success message
        first_item = order.items.first()
        if first_item:
            messages.success(request, "Thank you! Your review has been registered.")
            return redirect('food_de', slug=first_item.product.slug)
        return redirect('menu')
    
    if request.method == 'POST':
        # Get products from the order
        products = [item.product for item in order.items.all()]
        rating = int(request.POST.get('rating', 5))
        comment = (request.POST.get('comment') or '').strip()
        images = request.FILES.getlist('images')
        
        # Create a review for each product in the order
        for product in products:
            try:
                ReviewService.create_review(
                    product.slug,
                    {'rating': rating, 'comment': comment},
                    images if product == products[0] else [],
                    order.user
                )
            except Exception as e:
                print(f"Error creating review for {product}: {e}")
        
        # Mark review request as submitted
        review_request.is_submitted = True
        review_request.save()
        
        messages.success(request, "Thank you! Your reviews have been submitted for approval.")
        
        # Redirect to the first product's page
        if products:
            return redirect('food_de', slug=products[0].slug)
        return redirect('menu')
    
    return render(request, 'freshbread/order_review.html', {
        'review_request': review_request,
        'order': order
    })
