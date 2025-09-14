# UPI Payment Approval Feature

## Overview
This feature implements a manual approval system for UPI payments. When customers pay via UPI, their orders start with "pending" status and require admin approval before proceeding to the normal order workflow.

## How It Works

### 1. Customer Experience

#### **UPI Order Placement**
- Customer selects UPI as payment method
- Completes order as normal
- Order is created with **"pending"** status instead of "processing"
- Customer receives confirmation showing payment is awaiting approval

#### **Order Status Flow for UPI**
```
UPI Order:   pending → processing → shipped → delivered
Other Orders: processing → shipped → delivered
```

#### **Customer Notifications**
- **Order Success Page**: Shows special message for UPI orders about pending approval
- **Order Confirmation Email**: Includes UPI payment notice
- **Order Tracking**: Shows "Payment Approval" step in timeline for UPI orders
- **Status Update Email**: Sent when admin approves the payment

### 2. Admin Experience

#### **Admin Panel Management**
- Navigate to **Admin Panel → Store → Orders**
- Filter orders by status "pending" to see UPI orders awaiting approval
- Use bulk action **"Approve selected UPI orders"**

#### **Admin Actions Available**
1. **Approve UPI Orders** (pending → processing)
   - Moves orders to processing status
   - Sends notification email to customers
   - Orders then follow normal workflow

2. **Mark as Shipped** (processing → shipped)
3. **Mark as Delivered** (shipped → delivered)
4. **Process Returns** (for returned orders)

### 3. Automated Systems

#### **Daily Status Updates**
- Management command runs daily: `python manage.py update_order_status`
- **Only processes orders in "processing" status** (not pending)
- UPI orders remain pending until manually approved

#### **Email Notifications**
- **Order Confirmation**: Different message for UPI vs other payments
- **Payment Approval**: Sent when admin approves UPI payment
- **Status Updates**: Normal flow after approval

## Technical Implementation

### Database Changes
- Added **"pending"** status to Order model
- Order status choices now include:
  - `pending`: Pending Payment Approval
  - `processing`: Processing
  - `shipped`: Shipped
  - `delivered`: Delivered
  - `cancelled`: Cancelled

### Code Changes

#### **Models** (`store/models.py`)
```python
ORDER_STATUS_CHOICES = [
    ('pending', 'Pending Payment Approval'),
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
]
```

#### **Order Creation** (`store/views.py`)
```python
# Determine initial order status based on payment method
initial_status = 'pending' if payment_method == 'upi' else 'processing'

order = Order.objects.create(
    # ... other fields ...
    status=initial_status,
)
```

#### **Admin Actions** (`store/admin.py`)
```python
def approve_upi_orders(modeladmin, request, queryset):
    """Admin action to approve UPI orders and move them to processing"""
    # Updates status and sends notification emails
```

### Template Updates

#### **Order Success Page**
- Shows different message for UPI orders
- Includes informational alert about pending approval

#### **Order Tracking**
- Adds "Payment Approval" step for UPI orders
- Shows current status in timeline
- Displays warning notice for pending UPI orders

#### **Email Templates**
- Order confirmation includes UPI payment notice
- Status update email for payment approval

## Usage Instructions

### For Admins

1. **Daily Order Management**
   ```bash
   # Access admin panel
   http://localhost:8000/admin/
   
   # Go to Store → Orders
   # Filter by status: "Pending Payment Approval"
   # Select orders to approve
   # Choose action: "Approve selected UPI orders"
   ```

2. **Manual Commands**
   ```bash
   # Update order statuses (runs daily automatically)
   python manage.py update_order_status
   ```

### For Developers

1. **Database Migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Testing UPI Orders**
   - Create test order with UPI payment
   - Verify it starts with "pending" status
   - Test admin approval process
   - Confirm email notifications

## Benefits

### **Security**
- Manual verification prevents fraudulent orders
- Admin control over payment processing
- Clear audit trail of approvals

### **Customer Experience**
- Clear communication about approval process
- Email notifications keep customers informed
- Transparent order tracking

### **Business Control**
- Flexible payment processing
- Ability to verify payments before fulfillment
- Reduced risk of chargebacks

## Files Modified

### Core Files
- `store/models.py` - Added pending status
- `store/views.py` - Modified order creation logic
- `store/admin.py` - Added approval actions
- `store/management/commands/update_order_status.py` - Updated automation

### Templates
- `templates/store/order_success.html` - UPI order messaging
- `templates/store/track_order.html` - Payment approval timeline
- `templates/emails/order_confirmation.html` - UPI payment notice

### Migration Files
- `store/migrations/0017_alter_order_status.py` - Status field update

## Future Enhancements

1. **Automatic Approval**
   - Integration with UPI payment gateway APIs
   - Automatic verification based on transaction IDs

2. **Bulk Management**
   - Admin dashboard for payment verification
   - Bulk upload of approved transaction IDs

3. **Customer Self-Service**
   - Upload payment screenshots
   - Transaction ID submission form

4. **Advanced Notifications**
   - SMS notifications for order updates
   - Push notifications for mobile app

## Troubleshooting

### Common Issues

1. **Orders stuck in pending**
   - Check admin panel for approval
   - Verify payment method is UPI
   - Ensure admin has proper permissions

2. **Email notifications not working**
   - Check email configuration in settings
   - Verify customer email addresses
   - Check Django logs for email errors

3. **Status not updating**
   - Run migrations if recently deployed
   - Check database permissions
   - Verify admin actions are working

### Support Commands

```bash
# Check pending orders
python manage.py shell
>>> from store.models import Order
>>> Order.objects.filter(status='pending', payment_method='upi').count()

# Manual status update
>>> order = Order.objects.get(id=ORDER_ID)
>>> order.status = 'processing'
>>> order.save()
```

This feature provides a robust, secure way to handle UPI payments while maintaining excellent customer communication and administrative control.