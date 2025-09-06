from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from store.models import Order


class Command(BaseCommand):
    help = 'Update order status to shipped after 1 day'

    def handle(self, *args, **options):
        # Get orders that are still processing and were created more than 1 day ago
        one_day_ago = timezone.now() - timedelta(days=1)
        
        orders_to_ship = Order.objects.filter(
            status='processing',
            created_at__lt=one_day_ago
        )
        
        updated_count = 0
        for order in orders_to_ship:
            order.mark_as_shipped()
            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Order #{order.id} marked as shipped')
            )
        
        if updated_count == 0:
            self.stdout.write(
                self.style.WARNING('No orders found to update')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {updated_count} orders to shipped status')
            )