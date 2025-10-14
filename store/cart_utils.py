from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Cart, CartItem, Product, Size


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For guest users, use session
        if not request.session.session_key:
            request.session.create()
        
        cart, created = Cart.objects.get_or_create(
            session_key=request.session.session_key
        )
    
    return cart


def add_to_cart(request, product_id, quantity=1, size_code=None):
    """Add product to cart or update quantity"""
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)

    # Validate quantity
    if quantity <= 0:
        raise ValueError("Quantity must be positive")

    # Resolve size if provided
    size_obj = None
    if size_code:
        try:
            size_obj = Size.objects.get(code=size_code)
        except Size.DoesNotExist:
            raise ValueError("Invalid size selected")

    # Use get_or_create with a lock to prevent race conditions
    with transaction.atomic():
        # Lock the product row to check stock
        product = Product.objects.select_for_update().get(id=product_id)

        # Validate size vs product configuration
        product_has_sizes = product.sizes.exists()
        if product_has_sizes and size_obj is None:
            raise ValueError("Please select a size for this product")
        if size_obj is not None and product_has_sizes and not product.sizes.filter(id=size_obj.id).exists():
            raise ValueError("Selected size is not available for this product")
        
        # Try to get or create the cart item
        cart_item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart,
            product=product,
            size=size_obj,
            defaults={'quantity': 0}  # Will be updated below
        )
        
        # Calculate new total quantity
        new_quantity = quantity if created else cart_item.quantity + quantity
        
        # Check stock availability
        if new_quantity > product.stock:
            raise ValueError(f"Insufficient stock. Available: {product.stock}, Requested: {new_quantity}")
        
        if created:
            # New item, set the quantity
            cart_item.quantity = quantity
            cart_item.save()
        else:
            # Item exists, update quantity safely
            cart_item.quantity = new_quantity
            cart_item.save()
    
    return cart_item


def update_cart_item(request, product_id, quantity, size_code=None):
    """Update cart item quantity"""
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # Resolve size if provided
    size_obj = None
    if size_code:
        try:
            size_obj = Size.objects.get(code=size_code)
        except Size.DoesNotExist:
            raise ValueError("Invalid size selected")

    with transaction.atomic():
        try:
            # Lock both product and cart item
            product = Product.objects.select_for_update().get(id=product_id)
            # Validate size vs product configuration
            product_has_sizes = product.sizes.exists()
            if product_has_sizes and size_obj is None:
                raise ValueError("Please select a size for this product")
            if size_obj is not None and product_has_sizes and not product.sizes.filter(id=size_obj.id).exists():
                raise ValueError("Selected size is not available for this product")

            cart_item = CartItem.objects.select_for_update().get(cart=cart, product=product, size=size_obj)
            
            if quantity <= 0:
                cart_item.delete()
                return None
            else:
                # Check stock availability
                if quantity > product.stock:
                    raise ValueError(f"Insufficient stock. Available: {product.stock}, Requested: {quantity}")
                
                cart_item.quantity = quantity
                cart_item.save()
                return cart_item
        except CartItem.DoesNotExist:
            return None


def remove_from_cart(request, product_id, size_code=None):
    """Remove product from cart"""
    cart = get_or_create_cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    try:
        size_obj = None
        if size_code:
            size_obj = Size.objects.get(code=size_code)
        cart_item = CartItem.objects.get(cart=cart, product=product, size=size_obj)
        cart_item.delete()
        return True
    except CartItem.DoesNotExist:
        return False


def get_cart_items(request):
    """Get all cart items for user/session"""
    cart = get_or_create_cart(request)
    return cart.items.all().select_related('product')


def get_cart_total(request):
    """Get cart total price and item count"""
    cart = get_or_create_cart(request)
    return {
        'total_price': cart.total_price,
        'total_items': cart.total_items,
        'item_count': cart.items.count()
    }


def clear_cart(request):
    """Clear all items from cart"""
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return True


def merge_carts(user, session_key):
    """Merge guest cart with user cart when user logs in"""
    with transaction.atomic():
        try:
            # Get guest cart
            guest_cart = Cart.objects.select_for_update().get(session_key=session_key, user=None)
            
            # Get or create user cart
            user_cart, created = Cart.objects.get_or_create(user=user)
            
            # Merge items from guest cart to user cart
            for guest_item in guest_cart.items.select_for_update().all():
                try:
                    # Check if user cart already has this product
                    user_item = user_cart.items.select_for_update().get(product=guest_item.product)
                    
                    # Check stock before merging
                    new_quantity = user_item.quantity + guest_item.quantity
                    if new_quantity > guest_item.product.stock:
                        # If stock insufficient, keep original user quantity
                        continue
                    
                    user_item.quantity = new_quantity
                    user_item.save()
                except CartItem.DoesNotExist:
                    # Create new item in user cart
                    if guest_item.quantity <= guest_item.product.stock:
                        CartItem.objects.create(
                            cart=user_cart,
                            product=guest_item.product,
                            quantity=guest_item.quantity
                        )
            
            # Delete guest cart
            guest_cart.delete()
            
            return user_cart
            
        except Cart.DoesNotExist:
            # No guest cart exists
            user_cart, created = Cart.objects.get_or_create(user=user)
            return user_cart
