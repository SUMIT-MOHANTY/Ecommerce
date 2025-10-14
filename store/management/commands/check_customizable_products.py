from django.core.management.base import BaseCommand
from django.db import connection
from store.models import Product, Category

class Command(BaseCommand):
    help = 'Check and setup customizable products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample',
            action='store_true',
            help='Create sample customizable products if none exist',
        )

    def handle(self, *args, **options):
        # Check current customizable products
        customizable_products = Product.objects.filter(can_customize=True)
        total_products = Product.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f'Found {customizable_products.count()} customizable products out of {total_products} total products')
        )

        if customizable_products.count() > 0:
            self.stdout.write('Customizable products:')
            for product in customizable_products:
                self.stdout.write(f'  - {product.name} (Category: {product.category.name if product.category else "None"})')
        else:
            self.stdout.write(self.style.WARNING('No customizable products found!'))

        # Show products by category
        categories = Category.objects.all()
        for category in categories:
            product_count = Product.objects.filter(category=category).count()
            customizable_count = Product.objects.filter(category=category, can_customize=True).count()
            if product_count > 0:
                self.stdout.write(f'Category "{category.name}": {customizable_count}/{product_count} customizable products')

        if options['create_sample'] and customizable_products.count() == 0:
            self.stdout.write('Creating sample customizable products...')

            # Create some sample customizable products if none exist
            sample_products = [
                {'name': 'Custom T-Shirt', 'price': 599, 'stock': 50},
                {'name': 'Personalized Mug', 'price': 299, 'stock': 30},
                {'name': 'Custom Cap', 'price': 399, 'stock': 25},
            ]

            # Try to find a category, create one if none exists
            category = Category.objects.first()
            if not category:
                category = Category.objects.create(name='General')

            for product_data in sample_products:
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    defaults={
                        'category': category,
                        'price': product_data['price'],
                        'stock': product_data['stock'],
                        'can_customize': True,
                        'description': f'Customizable {product_data["name"].lower()} for personalization'
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created: {product.name}')
                else:
                    # Update existing product to be customizable
                    product.can_customize = True
                    product.save()
                    self.stdout.write(f'  ✓ Updated: {product.name} (now customizable)')

        self.stdout.write(self.style.SUCCESS('Check complete!'))
