#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from store.models import Product

print("=== Making Products Customizable ===")

# Get all products
products = Product.objects.all()
print(f"Found {products.count()} products")

# Make some products customizable
customizable_products = [
    'BIO',  # T-shirt or clothing item
    'Nitesh Saw',  # Another clothing item
]

updated_count = 0
for product in products:
    if product.name in customizable_products or updated_count < 2:  # Make at least 2 customizable
        if not product.can_customize:
            product.can_customize = True
            product.save()
            print(f"✓ Made '{product.name}' customizable")
            updated_count += 1

if updated_count == 0:
    print("Making first 2 products customizable...")
    for i, product in enumerate(products[:2]):
        if not product.can_customize:
            product.can_customize = True
            product.save()
            print(f"✓ Made '{product.name}' customizable")
            updated_count += 1

print(f"\n✅ Updated {updated_count} products to be customizable")

# Verify the changes
customizable_count = Product.objects.filter(can_customize=True).count()
print(f"Total customizable products now: {customizable_count}")
