from django.shortcuts import redirect, render
from numpy import sort
from urllib3 import request
from ..decorators import admin_login_protect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from core.infrastructure.models import Product
from django.db.models import F, Q

@admin_login_protect
def manage_products(request):
    from core.application.services.product_service import ProductService
    products = ProductService.get_all_products()
    queryset = Product.objects.all()

    # جستجو
    q = request.GET.get('q')
    if q:
        queryset = queryset.filter(name__icontains=q)

    # فقط محصولات تخفیف‌دار
    if request.GET.get('discounted'):
        queryset = queryset.filter(
            original_price__gt=0,
            price__lt=F('original_price')
        )

    # مرتب‌سازی
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-price')

    context = {
        'products': queryset,
        'request': request,
    }
    return render(request, 'freshbread/product/manage_f.html', context)
@admin_login_protect
def add_product(request):
    from core.interfaces.forms.auth_forms import ProductForm
    from core.application.services.product_service import ProductService
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            images = request.FILES.getlist('images')
            try:
                ProductService.create_product(data, images)
                messages.success(request, 'Product added successfully.')
                return redirect('manage')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ProductForm()
    return render(request, 'freshbread/product/food_su.html', {'form': form})
@admin_login_protect
def edit_product(request, slug):
    from core.infrastructure.repositories.product_repository import ProductRepository
    from core.interfaces.forms.auth_forms import ProductForm
    from core.application.services.product_service import ProductService
    product = ProductRepository.get_product_by_slug(slug)
    if not product:
        messages.error(request, 'Product not found')
        return redirect('manage')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                data = form.cleaned_data
                if 'menu_image' not in request.FILES:
                    data['menu_image'] = product.menu_image
                ProductService.update_product(product.id, data)
                messages.success(request, 'Product updated successfully.')
                return redirect('manage')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = ProductForm(instance=product)
    return render(request, 'freshbread/product/edf.html', {'form': form, 'product': product})
@admin_login_protect
def delete_product(request, slug):
    from core.infrastructure.repositories.product_repository import ProductRepository
    from core.application.services.product_service import ProductService
    product = ProductRepository.get_product_by_slug(slug)
    if not product:
        messages.error(request, 'Product not found')
        return redirect('manage')
    if request.method == 'POST':
        try:
            ProductService.delete_product(product.id)
            messages.success(request, 'Product deleted successfully.')
            return redirect('manage')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('manage')
    return render(request, 'freshbread/product/manage_f.html', {'product': product})
