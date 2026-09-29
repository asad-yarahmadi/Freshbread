from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

@login_required
def locations_manage_view(request):
    from core.infrastructure.models import UserLocation
    locations = list(UserLocation.objects.filter(user=request.user).order_by('-updated_at'))
    return render(request, 'freshbread/order/locations_manage.html', { 'locations': locations })

@login_required
def location_add_view(request):
    from core.infrastructure.models import UserLocation, Profile
    from django.core.exceptions import ValidationError
    import requests
    if request.method == 'POST':
        addr = request.POST.get('address_line', '').strip()
        postal = request.POST.get('postal_code', '').strip()
        house = request.POST.get('house_number', '').strip()
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        receiver_is_user = request.POST.get('receiver_is_user') == 'on'
        receiver_name = request.POST.get('receiver_name', '').strip()
        receiver_phone = request.POST.get('receiver_phone', '').strip()
        try:
            if not lat or not lng:
                raise ValidationError('Please choose a location on the map.')
            # validate Ottawa street
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {"User-Agent": "FreshBreadApp/1.0 (contact@freshbread.com)"}
            info = requests.get(url, headers=headers, timeout=5).json()
            a = info.get('address', {})
            if not ((a.get('road') or a.get('pedestrian') or a.get('cycleway') or a.get('footway')) and a.get('city') == 'Ottawa'):
                raise ValidationError('Location must be on a street within Ottawa.')
            # lock fields after map
            if not addr or not postal or not house:
                raise ValidationError('Address, postal code, and house number are required.')
            if receiver_is_user:
                receiver_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
                prof = Profile.objects.filter(user=request.user).first()
                receiver_phone = (prof.phone if prof else '') or receiver_phone
            else:
                # basic validations
                if len(receiver_name) < 2:
                    raise ValidationError('Receiver name must be at least 2 characters.')
                if len(receiver_phone) < 7:
                    raise ValidationError('Receiver phone must be at least 7 digits.')
            UserLocation.objects.create(
                user=request.user,
                receiver_is_user=receiver_is_user,
                receiver_name=receiver_name or None,
                receiver_phone=receiver_phone or None,
                address_line=addr,
                postal_code=postal,
                house_number=house,
                latitude=lat,
                longitude=lng,
            )
            messages.success(request, 'Location added successfully.')
            return redirect('locations_manage')
        except ValidationError as e:
            messages.error(request, str(e))
    return render(request, 'freshbread/order/location_add.html')

@login_required
def location_edit_view(request, pk):
    from core.infrastructure.models import UserLocation
    import requests
    loc = UserLocation.objects.filter(id=pk, user=request.user).first()
    if not loc:
        messages.error(request, 'Location not found.')
        return redirect('locations_manage')
    if request.method == 'POST':
        addr = request.POST.get('address_line', '').strip()
        postal = request.POST.get('postal_code', '').strip()
        house = request.POST.get('house_number', '').strip()
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        receiver_is_user = request.POST.get('receiver_is_user') == 'on'
        receiver_name = request.POST.get('receiver_name', '').strip()
        receiver_phone = request.POST.get('receiver_phone', '').strip()
        try:
            if not lat or not lng:
                raise ValidationError('Please choose a location on the map.')
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
            headers = {"User-Agent": "FreshBreadApp/1.0 (contact@freshbread.com)"}
            info = requests.get(url, headers=headers, timeout=5).json()
            a = info.get('address', {})
            if not ((a.get('road') or a.get('pedestrian') or a.get('cycleway') or a.get('footway')) and a.get('city') == 'Ottawa'):
                raise ValidationError('Location must be on a street within Ottawa.')
            if not addr or not postal or not house:
                raise ValidationError('Address, postal code, and house number are required.')
            loc.receiver_is_user = receiver_is_user
            loc.receiver_name = receiver_name or None
            loc.receiver_phone = receiver_phone or None
            loc.address_line = addr
            loc.postal_code = postal
            loc.house_number = house
            loc.latitude = lat
            loc.longitude = lng
            loc.save()
            messages.success(request, 'Location updated.')
            return redirect('locations_manage')
        except ValidationError as e:
            messages.error(request, str(e))
    return render(request, 'freshbread/order/location_add.html', { 'edit': True, 'location': loc })

@login_required
def location_delete_view(request, pk):
    from core.infrastructure.models import UserLocation
    loc = UserLocation.objects.filter(id=pk, user=request.user).first()
    if not loc:
        messages.error(request, 'Location not found.')
    else:
        loc.delete()
        messages.success(request, 'Location deleted.')
    return redirect('locations_manage')
