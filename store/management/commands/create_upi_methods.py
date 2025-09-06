from django.core.management.base import BaseCommand
from store.models import UPIPaymentMethod


class Command(BaseCommand):
    help = 'Create default UPI payment methods'

    def handle(self, *args, **options):
        # Create default UPI payment methods
        upi_methods = [
            {
                'name': 'PhonePe',
                'code': 'phonepe',
                'upi_id': 'merchant@phonepe',
                'display_order': 1,
            },
            {
                'name': 'Paytm',
                'code': 'paytm',
                'upi_id': 'merchant@paytm',
                'display_order': 2,
            },
            {
                'name': 'Google Pay',
                'code': 'googlepay',
                'upi_id': 'merchant@gpay',
                'display_order': 3,
            },
        ]

        for method_data in upi_methods:
            try:
                upi_method, created = UPIPaymentMethod.objects.get_or_create(
                    code=method_data['code'],
                    defaults=method_data
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created UPI payment method: {upi_method.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'UPI payment method already exists: {upi_method.name}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {method_data["name"]}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully processed UPI payment methods')
        )