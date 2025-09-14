from django.core.management.base import BaseCommand
from store.models import Order, ReturnRequest, Wallet
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test return request and wallet functionality'
    
    def add_arguments(self, parser):
        parser.add_argument('--user-id', type=int, help='User ID to test with')
        parser.add_argument('--order-id', type=int, help='Order ID to test with')
    
    def handle(self, *args, **options):
        user_id = options.get('user_id')
        order_id = options.get('order_id')
        
        if not user_id or not order_id:
            self.stdout.write(self.style.ERROR('Please provide both --user-id and --order-id'))
            return
        
        try:
            user = User.objects.get(id=user_id)
            order = Order.objects.get(id=order_id, user=user)
            
            self.stdout.write(f'Testing with User: {user.username} (ID: {user.id})')
            self.stdout.write(f'Testing with Order: #{order.id} (Total: ₹{order.total_amount})')
            
            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=user)
            self.stdout.write(f'Wallet before: ₹{wallet.balance} (Created: {created})')
            
            # Check if return request exists
            try:
                return_request = ReturnRequest.objects.get(order=order)
                self.stdout.write(f'Return request exists: Status = {return_request.status}')
                
                if return_request.status == 'pending':
                    self.stdout.write('Approving return request...')
                    return_request.approve_return('Test approval')
                    
                    # Refresh wallet
                    wallet.refresh_from_db()
                    self.stdout.write(f'Wallet after approval: ₹{wallet.balance}')
                    
                    # Check transactions
                    transactions = wallet.transactions.all()[:5]
                    self.stdout.write(f'Recent transactions ({transactions.count()})')
                    for tx in transactions:
                        self.stdout.write(f'  {tx.transaction_type}: ₹{tx.amount} - {tx.description}')
                        
                else:
                    self.stdout.write(f'Return request status is {return_request.status}, cannot approve')
                    
            except ReturnRequest.DoesNotExist:
                self.stdout.write('No return request found for this order')
                
            # Check order status
            order.refresh_from_db()
            self.stdout.write(f'Order status: {order.status}, Returned: {order.is_returned}')
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Order with ID {order_id} not found for user {user_id}'))
