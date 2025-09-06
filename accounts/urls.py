from django.urls import path
from . import views
from .api_views import RegisterAPIView, MeAPIView

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('login/', views.custom_login, name='custom_login'),
    # API endpoints
    path('api/register/', RegisterAPIView.as_view(), name='api_register'),
    path('api/me/', MeAPIView.as_view(), name='api_me'),
]