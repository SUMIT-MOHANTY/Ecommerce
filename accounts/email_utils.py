from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """Send welcome email after successful registration"""
    if not user.email:
        return False
        
    try:
        subject = 'Welcome to Customise Clothing!'
        html_content = render_to_string('emails/welcome.html', {
            'user': user,
            'site_name': 'Customise Clothing'
        })
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_login_notification_email(user, request):
    """Send login notification email"""
    if not user.email:
        return False
        
    try:
        # Get user's IP address
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if ip_address:
            ip_address = ip_address.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
            
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        subject = 'Login Alert - Customise Clothing'
        html_content = render_to_string('emails/login_notification.html', {
            'user': user,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'site_name': 'Customise Clothing'
        })
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Login notification sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send login notification to {user.email}: {str(e)}")
        return False

def send_order_confirmation_email(order):
    """Send order confirmation email"""
    if not order.user or not order.user.email:
        return False
        
    try:
        subject = f'Order Confirmation #{order.id}'
        html_content = render_to_string('emails/order_confirmation.html', {
            'order': order,
            'user': order.user,
            'site_name': 'Customise Clothing'
        })
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Order confirmation sent to {order.user.email} for order #{order.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send order confirmation to {order.user.email}: {str(e)}")
        return False

def send_order_status_update_email(order, status_message):
    """Send order status update email"""
    if not order.user or not order.user.email:
        return False
        
    try:
        subject = f'Order Update #{order.id}'
        html_content = render_to_string('emails/order_status_update.html', {
            'order': order,
            'user': order.user,
            'status_message': status_message,
            'site_name': 'Customise Clothing'
        })
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Order status update sent to {order.user.email} for order #{order.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send order status update to {order.user.email}: {str(e)}")
        return False

def send_personalization_update_email(personalization, status):
    """Send personalization request update email"""
    if not personalization.user or not personalization.user.email:
        return False
        
    try:
        status_messages = {
            'admin_approved': 'Your customization request has been approved by our team!',
            'rejected': 'Unfortunately, your customization request could not be approved.',
            'order_accepted': 'Your customised item has been added to your cart!'
        }
        
        subject = f'Customization Update - {personalization.product.name}'
        html_content = render_to_string('emails/personalization_update.html', {
            'personalization': personalization,
            'user': personalization.user,
            'status_message': status_messages.get(status, f'Status updated to: {status}'),
            'site_name': 'Customise Clothing'
        })
        text_content = strip_tags(html_content)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[personalization.user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Personalization update sent to {personalization.user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send personalization update to {personalization.user.email}: {str(e)}")
        return False


def send_email(to_email, subject, message):
    """Send a simple text/html email"""
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        msg.attach_alternative(message, "text/html")
        msg.send()
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False