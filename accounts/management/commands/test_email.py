from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.email_utils import send_welcome_email, send_login_notification_email

class Command(BaseCommand):
    help = 'Test email functionality by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test email to')
        parser.add_argument('--type', type=str, choices=['welcome', 'login'], default='welcome', help='Type of email to send')

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        if not email:
            self.stdout.write(self.style.ERROR('Please provide an email address using --email'))
            return
        
        # Create a test user for email purposes
        test_user, created = User.objects.get_or_create(
            username='test_email_user',
            defaults={
                'email': email,
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if not created:
            test_user.email = email
            test_user.save()
        
        if email_type == 'welcome':
            success = send_welcome_email(test_user)
            if success:
                self.stdout.write(self.style.SUCCESS(f'Welcome email sent successfully to {email}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send welcome email to {email}'))
        
        elif email_type == 'login':
            # Create a mock request object
            class MockRequest:
                META = {
                    'HTTP_X_FORWARDED_FOR': '127.0.0.1',
                    'HTTP_USER_AGENT': 'Test Browser'
                }
            
            mock_request = MockRequest()
            success = send_login_notification_email(test_user, mock_request)
            if success:
                self.stdout.write(self.style.SUCCESS(f'Login notification email sent successfully to {email}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send login notification email to {email}'))