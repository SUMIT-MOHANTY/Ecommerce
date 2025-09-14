from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, CustomizationRequest, Category, PersonalizationRequest, Order, OrderItem, Wallet, WalletTransaction, UPIPaymentMethod, UserAddress, ReturnRequest
from .cart_utils import get_cart_items, get_cart_total, clear_cart
from django import forms
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from accounts.email_utils import send_order_confirmation_email, send_personalization_update_email
import json

# Create your views here.

def home(request):
    # Get products and top-level categories (parent is null)
    products = Product.objects.all()

    # Dynamic Fandom section: children of a parent category named "Fandom & Superhero Edition"
    fandom_parent = Category.objects.filter(name__iexact='Fandom & Superhero Edition').first()

    # Top-level categories for the grid, EXCLUDING the fandom parent so it only appears in the fandom section
    if fandom_parent:
        categories = Category.objects.filter(parent__isnull=True).exclude(id=fandom_parent.id)
    else:
        categories = Category.objects.filter(parent__isnull=True)

    # Featured products (show at least 20 products if available)
    featured_products = products[:20]  # Show up to 20 products
    has_more_products = products.count() > 20

    fandoms = fandom_parent.children.all() if fandom_parent else []

    return render(request, 'store/home.html', {
        'featured_products': featured_products,
        'categories': categories,
        'fandoms': fandoms,
        'fandom_parent': fandom_parent,
        'has_more_products': has_more_products,
    })

from django.shortcuts import get_object_or_404

def category_page(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category)
    return render(request, 'store/category_page.html', {
        'category': category,
        'products': products
    })

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

def personal_customize_products(request):
    # List of customizable products
    products = [
        {'id': 1, 'name': 'T-shirt', 'image': 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=400&q=80'},
        {'id': 2, 'name': 'Mug', 'image': 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80'},
        {'id': 3, 'name': 'Bottle', 'image': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=400&q=80'},
        {'id': 4, 'name': 'Cap', 'image': 'https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=400&q=80'},
    ]
    return render(request, 'store/personal_customize_products.html', {'products': products})

class CustomizationRequestForm(forms.ModelForm):
    class Meta:
        model = CustomizationRequest
        fields = ['uploaded_image']

@login_required
def customize_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = CustomizationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            customization = form.save(commit=False)
            customization.user = request.user
            customization.product = product
            customization.save()
            return redirect('store:cart')
    else:
        form = CustomizationRequestForm()
    return render(request, 'store/customize_product.html', {'product': product, 'form': form})

# New Personalization Views
def personalize_products(request):
    """Show personalization product categories"""
    # Get all products that can be customized, grouped by category
    customizable_products = Product.objects.filter(can_customize=True).select_related('category')
    
    # Group products by category
    categories_with_products = {}
    for product in customizable_products:
        category_name = product.category.name if product.category else 'General'
        if category_name not in categories_with_products:
            categories_with_products[category_name] = []
        categories_with_products[category_name].append(product)
    
    # Create category cards with sample product info
    category_cards = []
    for category_name, products in categories_with_products.items():
        if products:
            # Use the first product's image as category image
            sample_product = products[0]
            category_cards.append({
                'name': category_name,
                'image': sample_product.image.url if sample_product.image else 'https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=400&q=80',
                'product_count': len(products),
                'min_price': min(p.price for p in products),
                'max_price': max(p.price for p in products),
                'products': products
            })
    
    return render(request, 'store/personalize_products.html', {
        'category_cards': category_cards,
        'categories_with_products': categories_with_products
    })

def personalize_category_products(request, category_name):
    """Show all customizable products within a specific category"""
    # Get all customizable products in this category
    products = Product.objects.filter(
        can_customize=True,
        category__name=category_name
    ).select_related('category')
    
    if not products.exists():
        # If no products found, try to find by category name (case insensitive)
        products = Product.objects.filter(
            can_customize=True,
            category__name__iexact=category_name
        ).select_related('category')
    
    return render(request, 'store/personalize_category_products.html', {
        'category_name': category_name,
        'products': products
    })

class PersonalizationRequestForm(forms.ModelForm):
    class Meta:
        model = PersonalizationRequest
        fields = ['uploaded_image']

@login_required
def personalize_product(request, product_id):
    """Personalization form for specific product"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = PersonalizationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            personalization = form.save(commit=False)
            personalization.user = request.user
            personalization.product = product
            personalization.save()
            return redirect('store:cart')
    else:
        form = PersonalizationRequestForm()
    return render(request, 'store/personalize_product.html', {'product': product, 'form': form})

@login_required
def submit_personalization(request):
    """Submit personalization request via AJAX"""
    if request.method == 'POST':
        form = PersonalizationRequestForm(request.POST, request.FILES)
        if form.is_valid():
            personalization = form.save(commit=False)
            personalization.user = request.user
            personalization.product_id = request.POST.get('product_id')
            personalization.save()
            return JsonResponse({'success': True, 'message': 'Personalization request submitted successfully!'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def remove_personalization(request):
    """User removes a personalization request from their cart view (delete the request)."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            personalization = get_object_or_404(PersonalizationRequest, id=request_id, user=request.user)
            
            # Do not allow removal if already accepted as order
            if personalization.status == 'order_accepted':
                return JsonResponse({'success': False, 'error': 'Cannot remove: order already accepted.'})
            
            personalization.delete()
            return JsonResponse({'success': True, 'message': 'Personalization request removed.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@user_passes_test(lambda u: u.is_staff)
def admin_accept_order(request):
    """Admin accepts user order for a personalization (after user_approved). Adds product to user's cart and marks status order_accepted."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            personalization = get_object_or_404(PersonalizationRequest, id=request_id)
            
            if personalization.status != 'user_approved':
                return JsonResponse({'success': False, 'error': 'Order not requested by user yet.'})
            
            # Add item to the user's cart directly
            from .models import Cart, CartItem
            cart, _ = Cart.objects.get_or_create(user=personalization.user)
            item, created = CartItem.objects.get_or_create(cart=cart, product=personalization.product, defaults={'quantity': 1})
            if not created:
                item.quantity += 1
                item.save()
            
            personalization.status = 'order_accepted'
            personalization.save()
            
            return JsonResponse({'success': True, 'message': 'Order accepted and item added to user\'s cart.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def approve_personalization(request):
    """User approves the admin-approved design and marks it as ready for cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            
            personalization = get_object_or_404(PersonalizationRequest, id=request_id, user=request.user)
            
            if personalization.status == 'admin_approved' and personalization.admin_final_image:
                # Mark as order accepted (ready for cart) and set initial quantity
                personalization.status = 'order_accepted'
                personalization.cart_quantity = 1
                personalization.save()
                
                # Send email notification about personalization status
                if personalization.user.email:
                    send_personalization_update_email(personalization, 'order_accepted')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Design approved and ready for cart!',
                    'personalization_id': personalization.id,
                    'product_price': float(personalization.product.price)
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot order: Design not ready or not admin approved'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@user_passes_test(lambda u: u.is_staff)
def admin_approve_personalization(request):
    """Admin approve personalization request and upload final design"""
    if request.method == 'POST':
        try:
            request_id = request.POST.get('request_id')
            final_image = request.FILES.get('final_image')
            notes = request.POST.get('notes', '')
            
            personalization = get_object_or_404(PersonalizationRequest, id=request_id)
            
            if final_image:
                personalization.admin_final_image = final_image
                personalization.admin_notes = notes
                personalization.status = 'admin_approved'
                personalization.save()
                
                # Send email notification about admin approval
                if personalization.user.email:
                    send_personalization_update_email(personalization, 'admin_approved')
                
                return JsonResponse({
                    'success': True,
                    'message': 'Personalization request approved successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Final image is required'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@user_passes_test(lambda u: u.is_staff)
def admin_reject_personalization(request):
    """Admin reject personalization request"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            
            personalization = get_object_or_404(PersonalizationRequest, id=request_id)
            personalization.status = 'rejected'
            personalization.save()
            
            # Send email notification about rejection
            if personalization.user.email:
                send_personalization_update_email(personalization, 'rejected')
            
            return JsonResponse({
                'success': True,
                'message': 'Personalization request rejected successfully!'
            })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@user_passes_test(lambda u: u.is_staff)
def update_admin_notes(request):
    """Update admin notes for personalization request"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            notes = data.get('notes', '')
            
            personalization = get_object_or_404(PersonalizationRequest, id=request_id)
            personalization.admin_notes = notes
            personalization.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Notes updated successfully!'
            })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def sports(request):
    return render(request, 'store/category_page.html', {'category': 'Sports (Cricket & Football)'})

def regional_preference(request):
    return render(request, 'store/category_page.html', {'category': 'Regional Preference'})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get related products from the same category (excluding current product)
    related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

def cart(request):
    return render(request, 'store/cart.html')

@login_required
def wallet_view(request):
    """Display user's wallet balance and transaction history"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all()[:20]  # Show last 20 transactions
    
    return render(request, 'store/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })


@login_required
def return_order(request, order_id):
    """Handle order return requests"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        try:
            order.process_return(reason)
            return render(request, 'store/return_success.html', {'order': order})
        except ValueError as e:
            return render(request, 'store/return_order.html', {
                'order': order,
                'error': str(e)
            })
    
    return render(request, 'store/return_order.html', {'order': order})


@login_required
def order_detail(request, order_id):
    """Display detailed order information including personalization images"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    personalization_images = order.get_personalization_images()
    
    return render(request, 'store/order_detail.html', {
        'order': order,
        'personalization_images': personalization_images
    })


@login_required
def track_order(request, order_id):
    """Display order tracking information"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    return render(request, 'store/track_order.html', {
        'order': order
    })


def all_products(request):
    products = Product.objects.all().order_by('-id')
    
    return render(request, 'store/all_products.html', {
        'products': products,
    })



    """Display all products with pagination"""
    products = Product.objects.all().order_by('-id')
    
    return render(request, 'store/all_products.html', {
        'products': products,
    })

@login_required
def checkout(request):
    """Unified checkout for standard and personalized items.
    - Validates stock for all items (cart items only - personalized items are now added directly to cart)
    - Creates Order and OrderItems, reduces stock, clears cart
    - Sets delivery_date = today + 5 days (static for now)
    """
    errors = []
    out_of_stock = []

    # Gather items from cart (includes both regular and personalized items)
    cart_items = get_cart_items(request)
    cart_total = get_cart_total(request)
    
    # Add personalized items to cart totals (same logic as cart_page)
    personalization_cart_total = Decimal('0.00')
    personalization_requests = []
    if request.user.is_authenticated:
        personalization_requests = PersonalizationRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'admin_approved', 'user_approved', 'order_accepted']
        ).select_related('product').order_by('-created_at')
        
        # Calculate total for personalized items in cart
        for req in personalization_requests:
            if req.is_in_cart:
                personalization_cart_total += req.cart_total_price
    
    # Calculate combined totals (including personalized items)
    combined_cart_total = {
        'total_price': cart_total['total_price'] + personalization_cart_total,
        'total_items': cart_total['total_items'] + sum(req.cart_quantity for req in personalization_requests if req.is_in_cart),
        'item_count': cart_total['item_count'] + sum(1 for req in personalization_requests if req.is_in_cart)
    }

    # Get active UPI payment methods
    upi_payment_methods = UPIPaymentMethod.objects.filter(is_active=True).order_by('display_order')

    # Get user wallet if authenticated
    user_wallet = None
    if request.user.is_authenticated:
        user_wallet, created = Wallet.objects.get_or_create(user=request.user)

    # Get personalization requests that are NOT in cart (only show pending personalized items)
    # Get user's saved addresses
    saved_addresses = []
    default_address = None
    if request.user.is_authenticated:
        saved_addresses = UserAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        default_address = saved_addresses.filter(is_default=True).first()
    
    # Get personalization requests that are NOT in cart (only show pending personalized items)
    personalization_items = []
    personalization_total = Decimal('0.00')
    if request.user.is_authenticated:
        # Get cart items to exclude personalized items already in cart
        cart_product_ids = [item.product.id for item in cart_items]
        personalization_items = list(
            PersonalizationRequest.objects.filter(
                user=request.user,
                status='admin_approved'  # Only show admin approved but not yet added to cart
            ).exclude(
                product_id__in=cart_product_ids  # Exclude items already in cart
            ).select_related('product')
        )
        # Calculate personalization items total
        personalization_total = sum(item.product.price for item in personalization_items)

    if request.method == 'POST':
        # Read address + payment
        full_name = request.POST.get('full_name', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        address_line2 = request.POST.get('address_line2', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        phone = request.POST.get('phone', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')
        upi_provider = request.POST.get('upi_provider', '')
        use_wallet = request.POST.get('use_wallet') == 'on'
        wallet_amount = Decimal(request.POST.get('wallet_amount', '0.00') or '0.00')

        # Basic validation
        required_fields = [full_name, address_line1, city, state, postal_code, phone]
        if not all(required_fields):
            errors.append('Please fill in all required fields.')

        # Compute totals and validate stock (only cart items)
        total_amount = Decimal('0.00')
        # Check cart items (includes personalized items that were added to cart)
        for item in cart_items:
            product = item.product
            qty = item.quantity
            if product.stock < qty:
                out_of_stock.append(f"{product.name} (need {qty}, have {product.stock})")
            total_amount += item.total_price
        
        # Add personalized items total to cart total
        total_amount += personalization_cart_total

        # Add COD charges if COD payment method is selected
        if payment_method == 'cod':
            total_amount += Decimal('30.00')  # ₹30 COD charge
            
        # Handle wallet payment
        wallet_amount_to_use = Decimal('0.00')
        remaining_amount = total_amount
        final_payment_method = payment_method
        
        if use_wallet and request.user.is_authenticated and user_wallet:
            # Validate wallet amount
            if wallet_amount > user_wallet.balance:
                errors.append(f'Insufficient wallet balance. Available: ₹{user_wallet.balance}')
            elif wallet_amount > total_amount:
                errors.append('Wallet amount cannot exceed total order amount.')
            else:
                wallet_amount_to_use = wallet_amount
                remaining_amount = total_amount - wallet_amount_to_use
                
                # Set payment method based on wallet usage
                if remaining_amount == 0:
                    final_payment_method = 'wallet'
                else:
                    final_payment_method = 'wallet_partial'

        if out_of_stock:
            errors.append('Some items are out of stock. Please remove them or try later:')

        if errors:
            return render(request, 'store/checkout.html', {
                'cart_items': cart_items,
                'personalization_items': personalization_items,
                'personalization_total': personalization_total,
                'cart_total': combined_cart_total,  # Use combined totals
                'upi_payment_methods': upi_payment_methods,
                'user_wallet': user_wallet,
                'errors': errors,
                'out_of_stock': out_of_stock,
                'form': {
                    'full_name': full_name,
                    'address_line1': address_line1,
                    'address_line2': address_line2,
                    'city': city,
                    'state': state,
                    'postal_code': postal_code,
                    'phone': phone,
                    'payment_method': payment_method,
                }
            })

        # Determine initial order status based on payment method
        initial_status = 'pending' if payment_method == 'upi' else 'processing'
        
        # Create order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=None if request.user.is_authenticated else getattr(request, 'session', None) and request.session.session_key,
            full_name=full_name,
            address_line1=address_line1,
            address_line2=address_line2 or '',
            city=city,
            state=state,
            postal_code=postal_code,
            phone=phone,
            payment_method=final_payment_method,
            upi_provider=upi_provider if payment_method == 'upi' else None,
            total_amount=total_amount,
            wallet_amount_used=wallet_amount_to_use,
            remaining_amount=remaining_amount,
            delivery_date=timezone.now().date() + timedelta(days=5),
            status=initial_status,
        )
        
        # Save address for authenticated users
        if request.user.is_authenticated:
            # Check if address already exists
            existing_address = UserAddress.objects.filter(
                user=request.user,
                full_name=full_name,
                address_line1=address_line1,
                address_line2=address_line2 or '',
                city=city,
                state=state,
                postal_code=postal_code,
                phone=phone
            ).first()
            
            if not existing_address:
                # Create new address
                UserAddress.objects.create(
                    user=request.user,
                    full_name=full_name,
                    address_line1=address_line1,
                    address_line2=address_line2 or '',
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    phone=phone,
                    is_default=not UserAddress.objects.filter(user=request.user).exists()  # Set as default if it's the first address
                )

        # Create order items and reduce stock (only cart items)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
                line_total=item.total_price,
            )
            # reduce stock
            item.product.stock = max(0, item.product.stock - item.quantity)
            item.product.save(update_fields=['stock'])
        
        # Create order items for personalized items in cart
        if request.user.is_authenticated:
            personalized_items_in_cart = PersonalizationRequest.objects.filter(
                user=request.user,
                status='order_accepted',
                cart_quantity__gt=0
            )
            for req in personalized_items_in_cart:
                OrderItem.objects.create(
                    order=order,
                    product=req.product,
                    product_name=req.product.name,
                    unit_price=req.product.price,
                    quantity=req.cart_quantity,
                    line_total=req.cart_total_price,
                )
                # reduce stock
                req.product.stock = max(0, req.product.stock - req.cart_quantity)
                req.product.save(update_fields=['stock'])
                # Reset cart quantity after order creation
                req.cart_quantity = 0
                req.save(update_fields=['cart_quantity'])
            
        # Process wallet payment if used
        if wallet_amount_to_use > 0 and user_wallet:
            user_wallet.deduct_money(
                wallet_amount_to_use,
                f"Payment for Order #{order.id}"
            )

        # Clear cart
        clear_cart(request)
        
        # Send order confirmation email
        if order.user and order.user.email:
            send_order_confirmation_email(order)

        return render(request, 'store/order_success.html', {'order': order})

    # GET: show checkout form and summary
    # Separate regular and personalized items in cart for display
    regular_cart_items = []
    personalized_cart_items = []
    
    if request.user.is_authenticated:
        # For now, let's simplify this:
        # Since we don't have a direct link between cart items and personalization requests,
        # and the issue is that products added normally are showing as personalized,
        # let's treat ALL cart items as regular items for the order summary
        # The personalized items will only show in the "Available for Approval" section
        regular_cart_items = cart_items
        personalized_cart_items = []  # Keep empty for now to fix the immediate issue
    else:
        # For guest users, all items are regular
        regular_cart_items = cart_items
    
    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'regular_cart_items': regular_cart_items,
        'personalized_cart_items': personalized_cart_items,
        'personalization_items': personalization_items,
        'cart_total': combined_cart_total,  # Use combined totals
        'upi_payment_methods': upi_payment_methods,
        'user_wallet': user_wallet,
        'saved_addresses': saved_addresses,
        'default_address': default_address,
    })

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'image', 'price', 'description', 'can_customize']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order categories and display hierarchical labels like "Parent › Child"
        self.fields['category'].queryset = Category.objects.all().order_by('parent__name', 'name')

        def make_label(cat: Category):
            return f"{cat.parent.name} › {cat.name}" if cat.parent else cat.name

        self.fields['category'].label_from_instance = make_label

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent', 'image', 'display_style']

@user_passes_test(lambda u: u.is_staff)
def shop_admin_dashboard(request):
    products = Product.objects.all()
    # Only show pending requests
    requests = CustomizationRequest.objects.select_related('user', 'product').filter(status='pending').order_by('-created_at')
    # Show all personalization requests, not just pending ones
    personalization_requests = PersonalizationRequest.objects.select_related('user', 'product').order_by('-created_at')
    categories = Category.objects.all()
    product_form = ProductForm()
    category_form = CategoryForm()
    return render(request, 'store/shop_admin_dashboard.html', {
        'products': products,
        'requests': requests,
        'personalization_requests': personalization_requests,
        'categories': categories,
        'product_form': product_form,
        'category_form': category_form,
    })

@user_passes_test(lambda u: u.is_staff)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    return redirect('store:shop_admin_dashboard')

@user_passes_test(lambda u: u.is_staff)
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('store:shop_admin_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/edit_product.html', {'form': form, 'product': product})

@user_passes_test(lambda u: u.is_staff)
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('store:shop_admin_dashboard')
    return render(request, 'store/delete_product.html', {'product': product})

@user_passes_test(lambda u: u.is_staff)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
    return redirect('store:shop_admin_dashboard')

@user_passes_test(lambda u: u.is_staff)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect('store:shop_admin_dashboard')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'store/edit_category.html', {'form': form, 'category': category})

@user_passes_test(lambda u: u.is_staff)
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('store:shop_admin_dashboard')
    return render(request, 'store/delete_category.html', {'category': category})

@user_passes_test(lambda u: u.is_staff)
def ajax_customization_requests(request):
    requests = CustomizationRequest.objects.select_related('user', 'product').filter(status='pending').order_by('-created_at')
    html = render_to_string('store/_customization_requests_table.html', {'requests': requests})
    return JsonResponse({'html': html})

@login_required
def update_personalization_cart_quantity(request):
    """Update quantity of personalized item in cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            quantity = int(data.get('quantity', 0))
            
            personalization = get_object_or_404(PersonalizationRequest, id=request_id, user=request.user)
            
            if personalization.status != 'order_accepted':
                return JsonResponse({'success': False, 'error': 'Item not in cart'})
            
            if quantity < 0:
                return JsonResponse({'success': False, 'error': 'Quantity must be non-negative'})
            
            # Check stock availability
            if quantity > personalization.product.stock:
                return JsonResponse({
                    'success': False, 
                    'error': f'Insufficient stock. Available: {personalization.product.stock}'
                })
            
            personalization.cart_quantity = quantity
            personalization.save()
            
            # Calculate combined cart totals
            from .cart_utils import get_cart_total
            cart_total = get_cart_total(request)
            
            # Add personalized items to cart totals
            personalized_total = Decimal('0.00')
            personalized_count = 0
            if request.user.is_authenticated:
                personalized_requests = PersonalizationRequest.objects.filter(
                    user=request.user,
                    status='order_accepted',
                    cart_quantity__gt=0
                )
                for req in personalized_requests:
                    personalized_total += req.cart_total_price
                    personalized_count += req.cart_quantity
            
            combined_cart_total = {
                'total_price': float(cart_total['total_price'] + personalized_total),
                'total_items': cart_total['total_items'] + personalized_count,
                'item_count': cart_total['item_count'] + len([req for req in PersonalizationRequest.objects.filter(
                    user=request.user,
                    status='order_accepted',
                    cart_quantity__gt=0
                ) if request.user.is_authenticated])
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Quantity updated successfully',
                'quantity': quantity,
                'total_price': float(personalization.cart_total_price),
                'item_removed': quantity == 0,
                'combined_cart_total': combined_cart_total
            })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def remove_personalization_from_cart(request):
    """Remove personalized item from cart"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_id = data.get('request_id')
            
            personalization = get_object_or_404(PersonalizationRequest, id=request_id, user=request.user)
            
            if personalization.status != 'order_accepted':
                return JsonResponse({'success': False, 'error': 'Item not in cart'})
            
            # Set quantity to 0 to remove from cart but keep the personalization request
            personalization.cart_quantity = 0
            personalization.save()
            
            # Calculate combined cart totals
            from .cart_utils import get_cart_total
            cart_total = get_cart_total(request)
            
            # Add personalized items to cart totals
            personalized_total = Decimal('0.00')
            personalized_count = 0
            if request.user.is_authenticated:
                personalized_requests = PersonalizationRequest.objects.filter(
                    user=request.user,
                    status='order_accepted',
                    cart_quantity__gt=0
                )
                for req in personalized_requests:
                    personalized_total += req.cart_total_price
                    personalized_count += req.cart_quantity
            
            combined_cart_total = {
                'total_price': float(cart_total['total_price'] + personalized_total),
                'total_items': cart_total['total_items'] + personalized_count,
                'item_count': cart_total['item_count'] + len([req for req in PersonalizationRequest.objects.filter(
                    user=request.user,
                    status='order_accepted',
                    cart_quantity__gt=0
                ) if request.user.is_authenticated])
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'combined_cart_total': combined_cart_total
            })
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def request_return(request, order_id):
    """Submit a return request for an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order can be returned
    if not order.can_be_returned:
        messages.error(request, 'This order cannot be returned.')
        return redirect('store:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        description = request.POST.get('description', '')
        
        if not reason:
            messages.error(request, 'Please select a reason for return.')
            return redirect('store:order_detail', order_id=order.id)
        
        try:
            # Create return request
            return_request = ReturnRequest.objects.create(
                order=order,
                user=request.user,
                reason=reason,
                description=description
            )
            
            messages.success(request, 'Return request submitted successfully. You will be notified once it is reviewed by our team.')
            return redirect('store:order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error submitting return request: {str(e)}')
            return redirect('store:order_detail', order_id=order.id)
    
    # GET request - show return form
    return render(request, 'store/return_request.html', {
        'order': order,
        'return_reasons': ReturnRequest.RETURN_REASON_CHOICES
    })


@login_required
def return_status(request, order_id):
    """View return request status"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not hasattr(order, 'return_request'):
        messages.error(request, 'No return request found for this order.')
        return redirect('store:order_detail', order_id=order.id)
    
    return render(request, 'store/return_status.html', {
        'order': order,
        'return_request': order.return_request
    })
