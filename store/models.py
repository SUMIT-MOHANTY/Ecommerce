from django.db import models, transaction
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Category(TimeStampedModel):
    DISPLAY_STYLE_CHOICES = [
        ('circle', 'Circle'),
        ('box', 'Box'),
    ]
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    display_style = models.CharField(
        max_length=10,
        choices=DISPLAY_STYLE_CHOICES,
        default='box',
        help_text='Choose how this category is displayed on the home page.'
    )

    def __str__(self):
        return self.name

    @property
    def has_children(self):
        return self.children.exists()


class Size(models.Model):
    CODE_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]
    code = models.CharField(max_length=4, choices=CODE_CHOICES, unique=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'code']

    def __str__(self):
        return self.code

class Product(TimeStampedModel):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(default=0, help_text='Available inventory')
    description = models.TextField(blank=True, help_text='Detailed product description')
    can_customize = models.BooleanField(default=False, help_text='Can this product be personalized?')
    # If a product has one or more sizes assigned via the Size model, size selection will be shown on PDP
    # Keep empty to indicate no size selection required
    # Admin can configure which products have sizes
    
    # defined after Size class (string reference)
    # ManyToMany allows selecting any subset of standard sizes
    sizes = models.ManyToManyField('Size', blank=True, related_name='products')

    def __str__(self):
        return self.name

class CustomizationRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    uploaded_image = models.ImageField(upload_to='custom_designs/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    final_image = models.ImageField(upload_to='final_designs/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.status})"


class PersonalizationRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('admin_approved', 'Admin Approved'),
        ('user_approved', 'User Approved'),
        ('order_accepted', 'Order Accepted'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    uploaded_image = models.ImageField(upload_to='personalization_designs/')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    admin_final_image = models.ImageField(upload_to='admin_final_designs/', blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    cart_quantity = models.PositiveIntegerField(default=0, help_text='Quantity in cart for order_accepted items')
    # Selected size for personalized item (optional)
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True, related_name='personalizations')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.status})"
    
    @property
    def is_in_cart(self):
        """Check if this personalization is in cart"""
        return self.status == 'order_accepted' and self.cart_quantity > 0
    
    @property
    def cart_total_price(self):
        """Get total price for cart quantity"""
        if self.is_in_cart:
            return self.product.price * self.cart_quantity
        return 0


class UserAddress(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=120)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False, help_text='Default address for checkout')
    
    class Meta:
        verbose_name = 'User Address'
        verbose_name_plural = 'User Addresses'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.full_name} ({self.city})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Cart(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Guest Cart {self.session_key}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    def get_or_create_item(self, product):
        """Get existing cart item or create new one with stock validation"""
        try:
            item = self.items.get(product=product)
            return item, False
        except CartItem.DoesNotExist:
            if product.stock <= 0:
                raise ValueError(f"Product '{product.name}' is out of stock")
            
            item = self.items.create(
                product=product,
                quantity=1
            )
            return item, True
    
    def add_item(self, product, quantity=1):
        """Add item to cart with stock validation"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        item, created = self.get_or_create_item(product)
        if not created:
            # Check if adding quantity exceeds stock
            new_quantity = item.quantity + quantity
            if new_quantity > product.stock:
                raise ValueError(f"Insufficient stock. Available: {product.stock}, Requested: {new_quantity}")
            item.quantity = new_quantity
            item.save()
        else:
            # New item, set the requested quantity
            if quantity > product.stock:
                raise ValueError(f"Insufficient stock. Available: {product.stock}, Requested: {quantity}")
            item.quantity = quantity
            item.save()
        
        return item
    
    @property
    def is_empty(self):
        """Check if cart is empty"""
        return self.items.count() == 0
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
    
    def get_item_count(self):
        """Get distinct item count (not total quantity)"""
        return self.items.count()


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('cart', 'product', 'size')
        indexes = [
            models.Index(fields=['cart', 'product', 'size']),
        ]
    
    def __str__(self):
        size_label = f" ({self.size.code})" if getattr(self, 'size', None) else ''
        return f"{self.quantity}x {self.product.name}{size_label}"
    
    @property
    def total_price(self):
        return self.quantity * self.product.price
    
    def increase_quantity(self, amount=1):
        """Increase item quantity safely"""
        with transaction.atomic():
            # Refresh from database and lock the row
            self.refresh_from_db()
            
            # Check stock availability
            new_quantity = self.quantity + amount
            if new_quantity > self.product.stock:
                raise ValueError(f"Insufficient stock. Available: {self.product.stock}, Current in cart: {self.quantity}")
            
            self.quantity = new_quantity
            self.save(update_fields=['quantity'])
    
    def decrease_quantity(self, amount=1):
        """Decrease item quantity, delete if reaches 0"""
        with transaction.atomic():
            # Refresh from database and lock the row
            self.refresh_from_db()
            
            new_quantity = self.quantity - amount
            
            if new_quantity <= 0:
                self.delete()
            else:
                self.quantity = new_quantity
                self.save(update_fields=['quantity'])
    
    def set_quantity(self, quantity):
        """Set specific quantity with stock validation"""
        if quantity <= 0:
            self.delete()
            return
        
        if quantity > self.product.stock:
            raise ValueError(f"Insufficient stock. Available: {self.product.stock}, Requested: {quantity}")
        
        self.quantity = quantity
        self.save(update_fields=['quantity'])


class Wallet(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.user.username}'s Wallet (₹{self.balance})"

    def add_money(self, amount, description=""):
        """Add money to wallet with transaction record"""
        with transaction.atomic():
            self.balance += Decimal(str(amount))
            self.save()
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='credit',
                amount=Decimal(str(amount)),
                description=description,
                balance_after=self.balance
            )
    
    def deduct_money(self, amount, description=""):
        """Deduct money from wallet with transaction record"""
        amount = Decimal(str(amount))
        if self.balance < amount:
            raise ValueError("Insufficient wallet balance")
        
        with transaction.atomic():
            self.balance -= amount
            self.save()
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='debit',
                amount=amount,
                description=description,
                balance_after=self.balance
            )


class WalletTransaction(TimeStampedModel):
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, default='')
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} ₹{self.amount}"


class UPIPaymentMethod(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True, help_text="e.g., PhonePe, Paytm, Google Pay")
    code = models.CharField(max_length=20, unique=True, help_text="e.g., phonepe, paytm, googlepay")
    logo = models.ImageField(upload_to='upi_logos/', help_text="Upload UPI app logo")
    qr_code = models.ImageField(upload_to='upi_qr_codes/', help_text="Upload QR code image for payments")
    upi_id = models.CharField(max_length=100, help_text="UPI ID for this payment method")
    is_active = models.BooleanField(default=True, help_text="Enable/disable this payment method")
    display_order = models.PositiveIntegerField(default=1, help_text="Order in which to display")
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name



class Order(TimeStampedModel):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending Payment Approval'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('upi', 'UPI Payment'),
        ('wallet', 'Wallet Payment'),
        ('wallet_partial', 'Wallet + Other Payment'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    full_name = models.CharField(max_length=120)
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='cod')
    upi_provider = models.CharField(max_length=20, blank=True, null=True)  # Store selected UPI provider
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wallet_amount_used = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=15, choices=ORDER_STATUS_CHOICES, default='processing')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    tracking_url = models.URLField(blank=True, null=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    return_reason = models.TextField(blank=True, null=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id}"

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def can_be_delivered(self):
        """Check if order can be marked as delivered"""
        return self.status == 'shipped'
    
    @property
    def can_be_returned(self):
        """Check if order can be returned"""
        return (self.status == 'delivered' and not self.is_returned and 
                not hasattr(self, 'return_request'))
    
    @property
    def has_pending_return(self):
        """Check if order has a pending return request"""
        return (hasattr(self, 'return_request') and 
                self.return_request.status == 'pending')
    
    def mark_as_shipped(self, tracking_number=None):
        """Mark order as shipped"""
        if self.status == 'processing':
            self.status = 'shipped'
            self.shipped_at = timezone.now()
            if tracking_number:
                self.tracking_number = tracking_number
            self.save()
    
    def mark_as_delivered(self):
        """Mark order as delivered and clean up personalized items from cart"""
        if self.status == 'shipped':
            self.status = 'delivered'
            self.delivered_at = timezone.now()
            self.save()
            
            # Remove personalized items from cart when order is delivered
            if self.user:
                self._cleanup_personalized_cart_items()
    
    def get_status_badge_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'processing': 'bg-warning',
            'shipped': 'bg-info',
            'delivered': 'bg-success',
            'cancelled': 'bg-danger',
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def _cleanup_personalized_cart_items(self):
        """Remove personalized items from cart when order is delivered"""
        from .models import Cart, CartItem, PersonalizationRequest
        
        try:
            # Get user's cart
            cart = Cart.objects.get(user=self.user)
            
            # Get all order items for this order
            order_product_ids = list(self.items.values_list('product_id', flat=True))
            
            # Find personalization requests for products in this order
            personalized_requests = PersonalizationRequest.objects.filter(
                user=self.user,
                product_id__in=order_product_ids,
                status='order_accepted'
            )
            
            # Remove corresponding cart items
            for request in personalized_requests:
                CartItem.objects.filter(
                    cart=cart,
                    product=request.product
                ).delete()
                
        except Cart.DoesNotExist:
            pass  # No cart exists, nothing to clean up
    
    def get_personalization_images(self):
        """Get personalization images specific to this order"""
        personalization_data = []
        
        for item in self.items.all():
            # Only show personalization details if user has exactly one 'order_accepted' 
            # personalization for this product to avoid showing wrong personalizations
            personalizations = PersonalizationRequest.objects.filter(
                user=self.user,
                product=item.product,
                status='order_accepted'
            )
            
            # Only show if there's exactly one personalization for this product
            # This ensures we don't show personalizations from other orders
            if personalizations.count() == 1:
                personalization = personalizations.first()
                personalization_data.append({
                    'product_name': item.product_name,
                    'user_image': personalization.uploaded_image,
                    'admin_image': personalization.admin_final_image,
                    'admin_notes': personalization.admin_notes,
                    'request_id': personalization.id
                })
        
        return personalization_data

    def process_return(self, reason=""):
        """Process order return and add refund to user's wallet"""
        if self.is_returned:
            raise ValueError("Order is already returned")
        
        if not self.user:
            raise ValueError("Cannot process return for guest orders")
        
        with transaction.atomic():
            # Mark order as returned
            self.is_returned = True
            self.return_reason = reason
            self.returned_at = timezone.now()
            self.save()
            
            # Add refund to user's wallet
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            refund_amount = self.total_amount
            wallet.add_money(
                refund_amount,
                f"Refund for returned Order #{self.id}"
            )


class ReturnRequest(TimeStampedModel):
    RETURN_STATUS_CHOICES = [
        ('pending', 'Pending Admin Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Refund Completed'),
    ]
    
    RETURN_REASON_CHOICES = [
        ('defective', 'Product is Defective'),
        ('wrong_item', 'Wrong Item Delivered'),
        ('not_as_described', 'Not as Described'),
        ('size_issue', 'Size Issue'),
        ('quality_issue', 'Quality Issue'),
        ('changed_mind', 'Changed Mind'),
        ('other', 'Other'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=RETURN_REASON_CHOICES)
    description = models.TextField(blank=True, help_text='Additional details about the return')
    status = models.CharField(max_length=15, choices=RETURN_STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    admin_notes = models.TextField(blank=True, help_text='Admin notes for this return request')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Return Request for Order #{self.order.id} - {self.status}"
    
    def approve_return(self, admin_notes=""):
        """Approve return request and process refund to wallet"""
        if self.status != 'pending':
            raise ValueError("Return request is not in pending status")
        
        with transaction.atomic():
            # Update return request status
            self.status = 'approved'
            self.approved_at = timezone.now()
            self.admin_notes = admin_notes
            self.refund_amount = self.order.total_amount
            self.save()
            
            # Update order status
            self.order.is_returned = True
            self.order.return_reason = self.get_reason_display()
            self.order.returned_at = timezone.now()
            self.order.save()
            
            # Add refund to user's wallet
            wallet, created = Wallet.objects.get_or_create(user=self.user)
            wallet.add_money(
                self.refund_amount,
                f"Refund for returned Order #{self.order.id} - {self.get_reason_display()}"
            )
            
            # Mark as completed
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
    
    def reject_return(self, admin_notes=""):
        """Reject return request"""
        if self.status != 'pending':
            raise ValueError("Return request is not in pending status")
        
        self.status = 'rejected'
        self.admin_notes = admin_notes
        self.save()


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
