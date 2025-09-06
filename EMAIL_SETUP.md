# Email Configuration Guide

## Current Setup (Development)
The system is currently configured to print emails to the console for development purposes.

## For Production (Gmail SMTP)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security > 2-Step Verification
   - App passwords > Generate password for "Mail"
3. **Update settings.py**:

```python
# Replace the console backend with SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-16-digit-app-password'  # Use app password, not regular password
```

## Testing Email Functionality

Run the test command to verify emails work:

```bash
# Test welcome email
python manage.py test_email --email your-email@gmail.com --type welcome

# Test login notification
python manage.py test_email --email your-email@gmail.com --type login
```

## Email Features Implemented

### Registration
- ✅ Welcome email sent when user registers with email address
- ✅ Email includes account details and getting started information

### Login
- ✅ Login notification email with security details (IP, browser, time)
- ✅ Automatic email sent on every login (if user has email)

### Orders
- ✅ Order confirmation email with order details, items, and totals
- ✅ Order status update emails (for future order tracking)

### Personalization
- ✅ Admin approval notification emails
- ✅ Admin rejection notification emails  
- ✅ Order acceptance notification emails

## Email Templates Location
All email templates are located in: `templates/emails/`
- `welcome.html` - Registration welcome email
- `login_notification.html` - Login security notification
- `order_confirmation.html` - Order confirmation
- `order_status_update.html` - Order status updates
- `personalization_update.html` - Personalization status updates

## Customization
- Modify email templates in `templates/emails/` for custom styling
- Update email utility functions in `accounts/email_utils.py`
- Configure different email backends in `settings.py`