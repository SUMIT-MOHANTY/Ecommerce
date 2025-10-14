#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from store.models import Product, Category

print("=== Product Database Check ===")
print(f"Total products: {Product.objects.count()}")

# Check customizable products
customizable_products = Product.objects.filter(can_customize=True)
print(f"Customizable products: {customizable_products.count()}")

if customizable_products.count() > 0:
    print("\nCustomizable products:")
    for product in customizable_products[:10]:  # Show first 10
        category_name = product.category.name if product.category else "No Category"
        print(f"  - {product.name} (₹{product.price}, Stock: {product.stock}) - Category: {category_name}")
else:
    print("\n❌ No customizable products found!")

# Check products by category
print("\n=== Products by Category ===")
categories = Category.objects.all()
for category in categories:
    product_count = Product.objects.filter(category=category).count()
    customizable_count = Product.objects.filter(category=category, can_customize=True).count()
    if product_count > 0:
        print(f'"{category.name}": {customizable_count}/{product_count} customizable products')

print("\n=== Sample Products to Make Customizable ===")
# Show some products that could be made customizable
sample_products = Product.objects.filter(can_customize=False)[:5]
if sample_products:
    print("Here are some products that could be made customizable:")
    for product in sample_products:
        print(f"  - {product.name} (ID: {product.id})")
    print("\nTo make them customizable, run:")
    print("  python manage.py shell")
    print("  >>> from store.models import Product")
    for product in sample_products:
        print(f"  >>> p = Product.objects.get(id={product.id}); p.can_customize = True; p.save()")
else:
    print("No products available to make customizable.")
