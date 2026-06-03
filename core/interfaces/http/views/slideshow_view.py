from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
from ..decorators import admin_login_protect
from django.contrib import messages
from core.infrastructure.models import SlideshowMode, Slide, SlideButton
from core.infrastructure.repositories.slideshow_repository import SlideshowRepository
from core.interfaces.forms.auth_forms import SlideshowModeForm, SlideForm, SlideButtonForm


@admin_login_protect
def manage_slideshow(request):
    active_mode = SlideshowRepository.get_active_slideshow()
    all_modes = SlideshowRepository.get_all_modes()
    
    context = {
        'active_mode': active_mode,
        'all_modes': all_modes,
    }
    return render(request, 'freshbread/slideshow/manage_slideshow.html', context)


@admin_login_protect
def set_active_slideshow(request, mode_id):
    mode = get_object_or_404(SlideshowMode, id=mode_id)
    # Check if mode has at least one slide
    if mode.slides.count() == 0:
        messages.error(request, 'Cannot activate a mode without any slides! Please add at least one slide first.')
        return redirect('manage_slideshow')
    SlideshowRepository.set_active_mode(mode)
    messages.success(request, 'Slideshow mode activated!')
    return redirect('manage_slideshow')


@admin_login_protect
def add_slideshow_mode(request):
    if request.method == 'POST':
        form = SlideshowModeForm(request.POST)
        if form.is_valid():
            mode = form.save(commit=False)
            mode.save()
            messages.success(request, 'Slideshow mode added!')
            return redirect('edit_slideshow_mode', mode_id=mode.id)
    else:
        form = SlideshowModeForm()
    return render(request, 'freshbread/slideshow/add_edit_slideshow_mode.html', {'form': form, 'is_edit': False})


@admin_login_protect
def edit_slideshow_mode(request, mode_id):
    mode = get_object_or_404(SlideshowMode.objects.prefetch_related('slides__buttons'), id=mode_id)
    
    if request.method == 'POST':
        form = SlideshowModeForm(request.POST, instance=mode)
        if form.is_valid():
            form.save()
            messages.success(request, 'Slideshow mode updated!')
            return redirect('manage_slideshow')
    else:
        form = SlideshowModeForm(instance=mode)
        
    context = {
        'form': form,
        'is_edit': True,
        'mode': mode,
        'slides': mode.slides.all(),
    }
    return render(request, 'freshbread/slideshow/add_edit_slideshow_mode.html', context)


@admin_login_protect
def delete_slideshow_mode(request, mode_id):
    mode = get_object_or_404(SlideshowMode, id=mode_id)
    if mode.is_default:
        messages.error(request, 'Cannot delete default mode!')
    else:
        # Check if this mode was active
        was_active = mode.is_active
        mode.delete()
        if was_active:
            # Activate default mode
            default_mode = SlideshowRepository.create_default_slideshow()
            SlideshowRepository.set_active_mode(default_mode)
            messages.info(request, 'Active mode was deleted. Default mode has been activated.')
        messages.success(request, 'Slideshow mode deleted!')
    return redirect('manage_slideshow')


@admin_login_protect
def add_slide(request, mode_id):
    mode = get_object_or_404(SlideshowMode, id=mode_id)
    if request.method == 'POST':
        form = SlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save(commit=False)
            slide.slideshow_mode = mode
            slide.save()
            messages.success(request, 'Slide added!')
            return redirect('edit_slideshow_mode', mode_id=mode.id)
    else:
        form = SlideForm()
    return render(request, 'freshbread/slideshow/add_edit_slide.html', {'form': form, 'is_edit': False, 'mode': mode})


@admin_login_protect
def edit_slide(request, slide_id):
    slide = get_object_or_404(Slide.objects.prefetch_related('buttons'), id=slide_id)
    if request.method == 'POST':
        form = SlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            form.save()
            messages.success(request, 'Slide updated!')
            return redirect('edit_slideshow_mode', mode_id=slide.slideshow_mode.id)
    else:
        form = SlideForm(instance=slide)
    return render(request, 'freshbread/slideshow/add_edit_slide.html', {'form': form, 'is_edit': True, 'mode': slide.slideshow_mode, 'slide': slide})


@admin_login_protect
def delete_slide(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    mode_id = slide.slideshow_mode.id
    slide.delete()
    messages.success(request, 'Slide deleted!')
    return redirect('edit_slideshow_mode', mode_id=mode_id)


@admin_login_protect
def add_slide_button(request, slide_id):
    slide = get_object_or_404(Slide, id=slide_id)
    if request.method == 'POST':
        form = SlideButtonForm(request.POST)
        if form.is_valid():
            btn = form.save(commit=False)
            btn.slide = slide
            btn.save()
            messages.success(request, 'Button added!')
            return redirect('edit_slide', slide_id=slide.id)
    else:
        form = SlideButtonForm()
    return render(request, 'freshbread/slideshow/add_edit_button.html', {'form': form, 'is_edit': False, 'slide': slide})


@admin_login_protect
def edit_slide_button(request, button_id):
    btn = get_object_or_404(SlideButton, id=button_id)
    if request.method == 'POST':
        form = SlideButtonForm(request.POST, instance=btn)
        if form.is_valid():
            form.save()
            messages.success(request, 'Button updated!')
            return redirect('edit_slide', slide_id=btn.slide.id)
    else:
        form = SlideButtonForm(instance=btn)
    return render(request, 'freshbread/slideshow/add_edit_button.html', {'form': form, 'is_edit': True, 'slide': btn.slide})


@admin_login_protect
def delete_slide_button(request, button_id):
    btn = get_object_or_404(SlideButton, id=button_id)
    slide_id = btn.slide.id
    btn.delete()
    messages.success(request, 'Button deleted!')
    return redirect('edit_slide', slide_id=slide_id)
