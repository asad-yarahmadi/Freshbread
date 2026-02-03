from core.interfaces.http.views.checkout_view import * 
from django.urls import path

urlpatterns=[
    path('checkout_step1/', checkout_s1, name='checkout_s1'),
    path('checkout_step2/', checkout_s2, name='checkout_s2'),
    path('checkout_paid/', checkout_paid, name='checkout_paid'),
    path('checkout_cancel/', checkout_cancel, name='checkout_cancel'),
    path('checkout_step3/', checkout_s3, name='checkout_s3'),
    path('checkout_success/', checkout_success, name='checkout_success'),
]