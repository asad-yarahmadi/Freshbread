"""
Forms for Authentication
فرم‌های مربوط به احراز هویت در Interface Layer
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User



class LoginForm(AuthenticationForm):
    """
    فرم ورود کاربر
    """
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری یا ایمیل'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class SignupForm(UserCreationForm):
    """
    فرم ثبت نام کاربر
    """
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خانوادگی'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور'
        })
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور'
        })


class EmailVerificationForm(forms.Form):
    """
    فرم تایید ایمیل
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل'
        })
    )
    verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد تایید ۶ رقمی'
        })
    )


class ProfileForm(forms.ModelForm):
    """
    فرم پروفایل کاربر
    """
    class Meta:
        from core.infrastructure.models import Profile
        model = Profile
        fields = ['phone', 'postal_code']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تلفن'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد پستی'
            })
        }


class PasswordResetForm(forms.Form):
    """
    فرم درخواست بازنشانی رمز عبور
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل'
        })
    )


class PasswordResetConfirmForm(forms.Form):
    """
    فرم تایید بازنشانی رمز عبور
    """
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور جدید'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور جدید'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند.")

        return cleaned_data


# ===== FORMS FROM ORIGINAL FORMS.PY =====

class MultiImageForm(forms.ModelForm):
    """
    فرم برای چندین تصویر (از forms.py اصلی)
    """
    class Meta:
        from core.infrastructure.models import ReviewImage
        model = ReviewImage
        fields = ['image']


class ProductForm(forms.ModelForm):
    """
    فرم محصول (از forms.py اصلی)
    """
    class Meta:
        from core.infrastructure.models import Product
        model = Product
        fields = [
            'name',
            'slug',
            'description',
            'original_price',
            'price',
            'menu_image',
            'category',
            'available'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'required': 'required'}),
            'slug': forms.TextInput(attrs={'required': 'required'}),
            'description': forms.Textarea(attrs={'rows': 4, 'required': 'required'}),
            'original_price': forms.NumberInput(attrs={'required': 'required'}),
            'price': forms.NumberInput(attrs={'required': 'required'}),
            'menu_image': forms.ClearableFileInput(attrs={'required': 'required'}),
            'category': forms.Select(attrs={'required': 'required'}),
            'available': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fname in ['name', 'slug', 'description', 'original_price', 'price', 'menu_image', 'category']:
            if fname in self.fields:
                self.fields[fname].required = True
        if 'available' in self.fields:
            self.fields['available'].required = False
            self.fields['available'].widget.attrs.pop('required', None)
        is_edit = getattr(self.instance, 'pk', None) is not None
        if is_edit and 'menu_image' in self.fields:
            self.fields['menu_image'].required = False
            self.fields['menu_image'].widget.attrs.pop('required', None)


class ReviewForm(forms.ModelForm):
    """
    فرم نظر (از forms.py اصلی)
    """
    class Meta:
        from core.infrastructure.models import Review
        model = Review
        fields = ['rating', 'comment', 'profile_image']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your feedback...'}),
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
        }