from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from decimal import Decimal
import json

from .models import Product, Cart, CartItem, PersonalizationRequest
from .cart_utils import (
    get_or_create_cart, add_to_cart, update_cart_item, 
    remove_from_cart, get_cart_items, get_cart_total, clear_cart
)


def cart_page(request):
    """Display cart page with all items"""
    cart_items = get_cart_items(request)
    cart_total = get_cart_total(request)
    
    # Get personalization requests for the user
    personalization_requests = []
    personalization_cart_total = Decimal('0.00')
    if request.user.is_authenticated:
        personalization_requests = PersonalizationRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'admin_approved', 'user_approved', 'order_accepted']
        ).select_related('product').order_by('-created_at')
        
        # Calculate total for personalized items in cart
        for req in personalization_requests:
            if req.is_in_cart:
                personalization_cart_total += req.cart_total_price
    
    # Calculate combined totals
    combined_cart_total = {
        'total_price': cart_total['total_price'] + personalization_cart_total,
        'total_items': cart_total['total_items'] + sum(req.cart_quantity for req in personalization_requests if req.is_in_cart),
        'item_count': cart_total['item_count'] + sum(1 for req in personalization_requests if req.is_in_cart)
    }
    
    context = {
        'cart_items': cart_items,
        'cart_total': combined_cart_total,
        'regular_cart_total': cart_total,
        'personalization_cart_total': personalization_cart_total,
        'personalization_requests': personalization_requests,
    }
    return render(request, 'store/cart.html', context)


@require_POST
def add_to_cart_ajax(request):
    """Add item to cart via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        size_code = data.get('size') or None


        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID required'})
        
        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'Quantity must be positive'})
        
        # Check if product exists and is in stock
        try:
            product = Product.objects.get(id=product_id)
            if product.stock <= 0:
                return JsonResponse({'success': False, 'error': f'Product "{product.name}" is out of stock'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        
        cart_item = add_to_cart(request, product_id, quantity, size_code)
        cart_total = get_cart_total(request)
        
        return JsonResponse({
            'success': True,
            'message': f'Added {quantity}x {cart_item.product.name} to cart',
            'cart_total': cart_total,
            'item': {
                'id': cart_item.id,
                'product_id': cart_item.product.id,
                'product_name': cart_item.product.name,
                'quantity': cart_item.quantity,
                'price': float(cart_item.product.price),
                'total_price': float(cart_item.total_price),
                'size': cart_item.size.code if cart_item.size else None,
            }
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})


@require_POST
def update_cart_ajax(request):
    """Update cart item quantity via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 0))
        size_code = data.get('size') or None
        
        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID required'})
        
        if quantity < 0:
            return JsonResponse({'success': False, 'error': 'Quantity cannot be negative'})
        
        # Check if product exists when quantity > 0
        if quantity > 0:
            try:
                product = Product.objects.get(id=product_id)
                if quantity > product.stock:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Insufficient stock. Available: {product.stock}'
                    })
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Product not found'})
        
        cart_item = update_cart_item(request, product_id, quantity, size_code)
        cart_total = get_cart_total(request)
        
        if cart_item is None:
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'cart_total': cart_total,
                'item_removed': True
            })
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully',
            'cart_total': cart_total,
            'item': {
                'id': cart_item.id,
                'product_id': cart_item.product.id,
                'quantity': cart_item.quantity,
                'total_price': float(cart_item.total_price),
                'size': cart_item.size.code if cart_item.size else None,
            }
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})


@require_POST
def remove_from_cart_ajax(request):
    """Remove item from cart via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        size_code = data.get('size') or None
        
        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID required'})
        
        success = remove_from_cart(request, product_id, size_code)
        cart_total = get_cart_total(request)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart successfully',
                'cart_total': cart_total
            })
        else:
            return JsonResponse({'success': False, 'error': 'Item not found in cart'})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})


def get_cart_data_ajax(request):
    """Get cart data for AJAX requests"""
    try:
        cart_items = get_cart_items(request)
        cart_total = get_cart_total(request)
        
        items_data = []
        for item in cart_items:
            # Safely get image URL
            image_url = ''
            try:
                if item.product.image and item.product.image.url:
                    image_url = item.product.image.url
            except ValueError:
                # Handle case where image field exists but no file is associated
                image_url = ''
            
            items_data.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'product_image': image_url,
                'product_description': item.product.description or '',
                'quantity': item.quantity,
                'price': float(item.product.price),
                'total_price': float(item.total_price),
                'size': item.size.code if item.size else None,
            })
        
        # Add personalization requests
        personalization_data = []
        if request.user.is_authenticated:
            personalization_requests = PersonalizationRequest.objects.filter(
                user=request.user,
                status__in=['pending', 'admin_approved', 'user_approved', 'order_accepted']
            ).select_related('product')
            
            for req in personalization_requests:
                personalization_data.append({
                    'id': req.id,
                    'product_id': req.product.id,
                    'product_name': req.product.name,
                    'status': req.status,
                    'uploaded_image': req.uploaded_image.url if req.uploaded_image else '',
                    'admin_final_image': req.admin_final_image.url if req.admin_final_image else '',
                    'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
                    'is_personalization': True,
                })
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'personalization_requests': personalization_data,
            'cart_total': cart_total
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def clear_cart_ajax(request):
    """Clear all items from cart via AJAX"""
    try:
        clear_cart(request)
        cart_total = get_cart_total(request)
        
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared successfully',
            'cart_total': cart_total
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})


def cart_count(request):
    """Get cart item count for navbar badge"""
    try:
        cart_total = get_cart_total(request)
        
        # Add personalized items to cart count
        personalized_count = 0
        if request.user.is_authenticated:
            personalized_requests = PersonalizationRequest.objects.filter(
                user=request.user,
                status='order_accepted',
                cart_quantity__gt=0
            )
            personalized_count = sum(req.cart_quantity for req in personalized_requests)
        
        total_count = cart_total['total_items'] + personalized_count
        
        return JsonResponse({
            'success': True,
            'count': total_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def validate_cart_stock(request):
    """Validate stock availability for all cart items"""
    try:
        cart_items = get_cart_items(request)
        stock_issues = []
        
        for item in cart_items:
            if item.quantity > item.product.stock:
                stock_issues.append({
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'requested': item.quantity,
                    'available': item.product.stock
                })
        
        return JsonResponse({
            'success': True,
            'has_issues': len(stock_issues) > 0,
            'stock_issues': stock_issues
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
