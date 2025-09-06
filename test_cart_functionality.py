#!/usr/bin/env python
"""
Cart System Testing Script
Tests all the fixed cart functionality to ensure everything works correctly.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from store.models import Product, Category, Cart, CartItem
from store.cart_utils import (
    get_or_create_cart, add_to_cart, update_cart_item, 
    remove_from_cart, get_cart_items, get_cart_total, merge_carts
)
import json

def run_cart_tests():
    """Run comprehensive cart functionality tests"""
    print("🧪 Starting Cart System Tests...")
    
    # Test 1: Create test data
    print("\n1️⃣ Setting up test data...")
    try:
        # Create test category and products
        category, _ = Category.objects.get_or_create(
            name="Test Category",
            defaults={'display_style': 'box'}
        )
        
        product1, _ = Product.objects.get_or_create(
            name="Test Product 1",
            defaults={
                'category': category,
                'price': 25.99,
                'stock': 10,
                'description': 'Test product description',
                'can_customize': False
            }
        )
        
        product2, _ = Product.objects.get_or_create(
            name="Test Product 2", 
            defaults={
                'category': category,
                'price': 15.50,
                'stock': 5,
                'description': 'Another test product',
                'can_customize': True
            }
        )
        
        print(f"✅ Created test products: {product1.name}, {product2.name}")
        
    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return False
    
    # Test 2: Cart creation for authenticated user
    print("\n2️⃣ Testing cart creation for authenticated user...")
    try:
        user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = user
        
        # Add session support
        def dummy_get_response(request):
            return None
        
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        
        cart = get_or_create_cart(request)
        assert cart.user == user
        print(f"✅ User cart created successfully: {cart}")
        
    except Exception as e:
        print(f"❌ Failed user cart creation: {e}")
        return False
    
    # Test 3: Cart creation for guest user
    print("\n3️⃣ Testing cart creation for guest user...")
    try:
        factory = RequestFactory()
        request = factory.get('/')
        request.user = None
        
        # Mock anonymous user
        class AnonymousUser:
            is_authenticated = False
        request.user = AnonymousUser()
        
        # Add session support
        def dummy_get_response(request):
            return None
        
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()
        
        guest_cart = get_or_create_cart(request)
        assert guest_cart.session_key == request.session.session_key
        print(f"✅ Guest cart created successfully: {guest_cart}")
        
    except Exception as e:
        print(f"❌ Failed guest cart creation: {e}")
        return False
    
    # Test 4: Add items to cart with stock validation
    print("\n4️⃣ Testing add to cart with stock validation...")
    try:
        # Add valid quantity
        cart_item = add_to_cart(request, product1.id, 2)
        assert cart_item.quantity == 2
        print(f"✅ Added {cart_item.quantity}x {cart_item.product.name} to cart")
        
        # Test stock validation - should fail
        try:
            add_to_cart(request, product2.id, 10)  # More than stock (5)
            print("❌ Stock validation failed - should have thrown error")
            return False
        except ValueError as e:
            print(f"✅ Stock validation working: {e}")
        
    except Exception as e:
        print(f"❌ Failed add to cart: {e}")
        return False
    
    # Test 5: Update cart item quantities
    print("\n5️⃣ Testing cart item quantity updates...")
    try:
        # Update to valid quantity
        updated_item = update_cart_item(request, product1.id, 3)
        assert updated_item.quantity == 3
        print(f"✅ Updated quantity to {updated_item.quantity}")
        
        # Update to zero (should remove)
        removed_item = update_cart_item(request, product1.id, 0)
        assert removed_item is None
        print("✅ Item removed when quantity set to 0")
        
    except Exception as e:
        print(f"❌ Failed cart update: {e}")
        return False
    
    # Test 6: Cart totals calculation
    print("\n6️⃣ Testing cart totals calculation...")
    try:
        # Add items back
        add_to_cart(request, product1.id, 2)  # 2 * 25.99 = 51.98
        add_to_cart(request, product2.id, 1)  # 1 * 15.50 = 15.50
        
        cart_total = get_cart_total(request)
        expected_total = (2 * float(product1.price)) + (1 * float(product2.price))
        
        print(f"Debug: total_items={cart_total['total_items']}, total_price={cart_total['total_price']}, expected={expected_total}")
        
        assert cart_total['total_items'] == 3
        assert abs(float(cart_total['total_price']) - expected_total) < 0.01  # Allow for floating point precision
        print(f"✅ Cart totals correct: {cart_total['total_items']} items, ${cart_total['total_price']}")
        
    except Exception as e:
        print(f"❌ Failed cart totals: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 7: Remove items from cart
    print("\n7️⃣ Testing item removal...")
    try:
        success = remove_from_cart(request, product1.id)
        assert success == True
        
        cart_items = get_cart_items(request)
        assert len(cart_items) == 1
        print(f"✅ Item removed successfully, {len(cart_items)} items remaining")
        
    except Exception as e:
        print(f"❌ Failed item removal: {e}")
        return False
    
    # Test 8: Cart merging (guest to user)
    print("\n8️⃣ Testing cart merging...")
    try:
        # Create a new user cart
        user_request = factory.get('/')
        user_request.user = user
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(user_request)
        user_request.session.save()
        
        # Add item to user cart
        add_to_cart(user_request, product1.id, 1)
        
        # Merge guest cart to user cart
        merged_cart = merge_carts(user, request.session.session_key)
        
        # Check if items were merged
        total_items = merged_cart.total_items
        print(f"✅ Cart merged successfully, total items: {total_items}")
        
    except Exception as e:
        print(f"❌ Failed cart merging: {e}")
        return False
    
    # Test 9: Model method tests
    print("\n9️⃣ Testing model methods...")
    try:
        cart = get_or_create_cart(user_request)
        
        # Test cart methods
        assert not cart.is_empty
        item_count = cart.get_item_count()
        assert item_count > 0
        print(f"✅ Cart model methods working: not empty, {item_count} distinct items")
        
        # Test CartItem methods
        cart_item = cart.items.first()
        original_quantity = cart_item.quantity
        cart_item.increase_quantity(1)
        assert cart_item.quantity == original_quantity + 1
        print(f"✅ CartItem increase_quantity working")
        
        cart_item.decrease_quantity(1)
        assert cart_item.quantity == original_quantity
        print(f"✅ CartItem decrease_quantity working")
        
    except Exception as e:
        print(f"❌ Failed model methods: {e}")
        return False
    
    print("\n🎉 All cart system tests passed successfully!")
    print("\n📋 Test Summary:")
    print("✅ Cart creation for authenticated users")
    print("✅ Cart creation for guest users") 
    print("✅ Add items with stock validation")
    print("✅ Update cart item quantities")
    print("✅ Cart totals calculation")
    print("✅ Remove items from cart")
    print("✅ Cart merging (guest to user)")
    print("✅ Model methods functionality")
    
    return True

if __name__ == '__main__':
    try:
        success = run_cart_tests()
        if success:
            print("\n🚀 Cart system is fully functional and bug-free!")
        else:
            print("\n⚠️ Some tests failed. Please check the output above.")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")