from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('plain-shirt/', views.plain_shirt, name='plain_shirt'),
    path('cap/', views.cap, name='cap'),
    path('bottle/', views.bottle, name='bottle'),
    path('mug/', views.mug, name='mug'),
    path('god-goddess/', views.god_goddess, name='god_goddess'),
    path('oversize/', views.oversize, name='oversize'),
    path('polo-shirt/', views.polo_shirt, name='polo_shirt'),
    path('regular-thin/', views.regular_thin, name='regular_thin'),
    path('regular-thick/', views.regular_thick, name='regular_thick'),
    path('combo/', views.combo, name='combo'),
    path('couple/', views.couple, name='couple'),
    path('women-specific/', views.women_specific, name='women_specific'),
    path('personal-customise/', views.personal_customise, name='personal_customise'),
    path('sports/', views.sports, name='sports'),
    path('regional-preference/', views.regional_preference, name='regional_preference'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
] 