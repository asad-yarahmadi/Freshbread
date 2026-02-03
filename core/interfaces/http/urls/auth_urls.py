from django.urls import path, include
from .. import views
from core.interfaces.http.views.auth_view import *
from core.interfaces.http.views.signup_view import *
from core.interfaces.http.views.reset_password_view import *
from core.interfaces.http.views.verify_email_view import *
from core.interfaces.http.views.social_auth_view import *
from core.interfaces.http.views.profile_view import *
urlpatterns = [
    path('Signup/', signup_view, name='Signup'),
    path('Login/', login_view, name='Login'),
    path('logout/', logout_view, name='logout'),

    # Password reset
    path('reset_password_step1/', reset_password_step1_view, name='reset_password_step1'),
    path('reset_password_step2/', reset_password_step2_view, name='reset_password_step2'),
    path('reset_password_step3/', reset_password_step3_view, name='reset_password_step3'),

    # Email & OAuth
    path('verify_email/', verify_email_view, name='verify_email'),
    path('oauth_google/', oauth_google_view, name='oauth_google'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('check_profile/', check_social_profile_view, name='check_social_profile_view'),
    path('complete_profile_social/', complete_social_profile_view, name='complete_social_profile_view'),
    path('complete_profile/', complete_profile_view, name='complete_profile'),
    
    # Admin / Auth pages
    path('su/', signup_view, name='su'),
    path('ru/', login_view , name='ru'),
]
