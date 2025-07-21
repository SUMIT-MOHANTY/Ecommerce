from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'store/home.html')

def plain_shirt(request):
    return render(request, 'store/category_page.html', {'category': 'Plain Shirt'})

def cap(request):
    return render(request, 'store/category_page.html', {'category': 'Cap'})

def bottle(request):
    return render(request, 'store/category_page.html', {'category': 'Bottle'})

def mug(request):
    return render(request, 'store/category_page.html', {'category': 'Mug'})

def god_goddess(request):
    return render(request, 'store/category_page.html', {'category': 'God & Goddess'})

def oversize(request):
    return render(request, 'store/category_page.html', {'category': 'Oversize'})

def polo_shirt(request):
    return render(request, 'store/category_page.html', {'category': 'Polo Shirt'})

def regular_thin(request):
    return render(request, 'store/category_page.html', {'category': 'Regular Thin'})

def regular_thick(request):
    return render(request, 'store/category_page.html', {'category': 'Regular Thick'})

def combo(request):
    return render(request, 'store/category_page.html', {'category': 'Combo'})

def couple(request):
    return render(request, 'store/category_page.html', {'category': 'Couple'})

def women_specific(request):
    return render(request, 'store/category_page.html', {'category': 'Women Specific'})

def personal_customise(request):
    return render(request, 'store/category_page.html', {'category': 'Personal Customise'})

def sports(request):
    return render(request, 'store/category_page.html', {'category': 'Sports (Cricket & Football)'})

def regional_preference(request):
    return render(request, 'store/category_page.html', {'category': 'Regional Preference'})

def product_detail(request, product_id):
    # Placeholder product data
    product = {
        'id': product_id,
        'name': f'Product {product_id}',
        'description': 'This is a detailed description of the product.',
        'price': 19.99,
        'image': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80',
        'is_on_sale': True,
        'discount_percentage': 20,
        'current_price': 15.99,
    }
    return render(request, 'store/product_detail.html', {'product': product})

def cart(request):
    return render(request, 'store/cart.html')

def checkout(request):
    return render(request, 'store/checkout.html')
