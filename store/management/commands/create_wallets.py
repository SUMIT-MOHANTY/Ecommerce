from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Wallet


class Command(BaseCommand):
    help = 'Create wallets for existing users'

    def handle(self, *args, **options):
        users_without_wallet = User.objects.filter(wallet__isnull=True)
        created_count = 0

        for user in users_without_wallet:
            wallet, created = Wallet.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created wallet for user: {user.username}')
                )

        if created_count == 0:
            self.stdout.write(
                self.style.WARNING('All users already have wallets')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} wallets')
            )