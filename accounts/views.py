from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegistrationForm, CustomLoginForm
from .models import UserProfile
from store.models import Order
from .email_utils import send_welcome_email, send_login_notification_email

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send welcome email if email is provided
            if user.email:
                send_welcome_email(user)
                messages.success(request, f'Account created successfully! A welcome email has been sent to {user.email}')
            else:
                messages.success(request, 'Account created successfully!')
            
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    """User profile page"""
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })

@login_required
def my_orders(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/my_orders.html', {
        'orders': orders
    })

def custom_login(request):
    """Custom login view that accepts email/mobile or username"""
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            login_field = form.cleaned_data['login_field']
            password = form.cleaned_data['password']
            
            user = None
            
            # Try to find user by email first
            if '@' in login_field:
                try:
                    user_by_email = User.objects.get(email__iexact=login_field)
                    user = authenticate(request, username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    pass
            # Try to find user by phone
            elif login_field.isdigit():
                try:
                    profile = UserProfile.objects.get(phone=login_field)
                    user = authenticate(request, username=profile.user.username, password=password)
                except UserProfile.DoesNotExist:
                    pass
            # Try username directly
            else:
                user = authenticate(request, username=login_field, password=password)
            
            if user is not None:
                auth_login(request, user)
                
                # Send login notification email if user has email
                if user.email:
                    send_login_notification_email(user, request)
                
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid credentials. Please check your email/mobile/username and password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'registration/login.html', {'form': form})
