from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import UserProfile
import re

PHONE_REGEX = re.compile(r"^[0-9]{7,15}$")

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=False, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text="Provide either email or mobile number (mandatory)."
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your mobile number'
        }),
        help_text="Provide either email or mobile number (mandatory)."
    )

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            if not PHONE_REGEX.match(phone):
                raise ValidationError("Enter a valid mobile number (digits only, 7-15 characters).")
            if UserProfile.objects.filter(phone=phone).exists():
                raise ValidationError("This mobile number is already registered.")
        return phone

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email", "").strip()
        phone = cleaned.get("phone", "").strip()

        if not email and not phone:
            raise ValidationError("Please provide either an email address or a mobile number (at least one is required).")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get("email", "").strip()
        phone = self.cleaned_data.get("phone", "").strip()
        if email:
            user.email = email
        if commit:
            user.save()
            if phone:
                UserProfile.objects.create(user=user, phone=phone)
        return user


class CustomLoginForm(forms.Form):
    """Custom login form that accepts email, mobile, or username"""
    login_field = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email, mobile number, or username',
            'autofocus': True
        }),
        label='Email / Mobile / Username'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        label='Password'
    )

    def clean_login_field(self):
        login_field = self.cleaned_data.get('login_field', '').strip()
        if not login_field:
            raise ValidationError('This field is required.')
        return login_field
