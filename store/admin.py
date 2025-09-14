from django.contrib import admin
from django import forms
from .models import Product, CustomizationRequest, Category, Cart, CartItem, PersonalizationRequest, Order, OrderItem, Wallet, WalletTransaction, UPIPaymentMethod

class CategoryInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 1
    fields = ('name', 'image', 'display_style')
    show_change_link = True

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'display_style')
    list_filter = ('parent', 'display_style')
    list_editable = ('display_style',)
    ordering = ('parent__name', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'parent', 'image', 'display_style')
        }),
    )
    inlines = [CategoryInline]
class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order categories and display hierarchical labels
        self.fields['category'].queryset = Category.objects.all().order_by('parent__name', 'name')

        def make_label(cat: Category):
            return f"{cat.parent.name}  {cat.name}" if cat.parent else cat.name

        self.fields['category'].label_from_instance = make_label

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'category', 'price', 'stock')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'price', 'stock', 'description')
        }),
        ('Images', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('total_price',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'session_key', 'total_items', 'total_price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('total_items', 'total_price', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('user', 'session_key')
        }),
        ('Summary', {
            'fields': ('total_items', 'total_price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'total_price', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('cart__user__username', 'product__name')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Item Information', {
            'fields': ('cart', 'product', 'quantity')
        }),
        ('Pricing', {
            'fields': ('total_price',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(CustomizationRequest)

@admin.register(PersonalizationRequest)
class PersonalizationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'product', 'status', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Request Info', {
            'fields': ('user', 'product', 'uploaded_image', 'status')
        }),
        ('Admin Response', {
            'fields': ('admin_final_image', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_display(self, obj):
        return obj.user.username if obj.user else '-'
    user_display.short_description = 'User'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('line_total',)


class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount', 'description', 'balance_after', 'created_at')
    can_delete = False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WalletTransactionInline]


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_user', 'transaction_type', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__username', 'description')
    readonly_fields = ('created_at',)
    
    def wallet_user(self, obj):
        return obj.wallet.user.username
    wallet_user.short_description = 'User'


def process_order_return(modeladmin, request, queryset):
    """Admin action to process order returns"""
    for order in queryset:
        if not order.is_returned and order.user:
            try:
                order.process_return("Processed by admin")
                modeladmin.message_user(request, f"Order #{order.id} return processed successfully.")
            except ValueError as e:
                modeladmin.message_user(request, f"Error processing return for Order #{order.id}: {str(e)}", level='ERROR')
        else:
            modeladmin.message_user(request, f"Order #{order.id} cannot be returned.", level='WARNING')

process_order_return.short_description = "Process selected order returns"


def approve_upi_orders(modeladmin, request, queryset):
    """Admin action to approve UPI orders and move them to processing"""
    from accounts.email_utils import send_order_status_update_email
    
    updated = 0
    for order in queryset:
        if order.status == 'pending' and order.payment_method == 'upi':
            order.status = 'processing'
            order.save(update_fields=['status'])
            updated += 1
            
            # Send notification email to customer
            if order.user and order.user.email:
                send_order_status_update_email(
                    order, 
                    "Your UPI payment has been verified and your order is now being processed!"
                )
    
    if updated > 0:
        modeladmin.message_user(request, f"Successfully approved {updated} UPI order(s). They are now in processing status and customers have been notified.")
    else:
        modeladmin.message_user(request, "No UPI orders were updated. Only pending UPI orders can be approved.", level='WARNING')

approve_upi_orders.short_description = "Approve selected UPI orders (pending → processing)"


def mark_orders_as_shipped(modeladmin, request, queryset):
    """Admin action to mark orders as shipped"""
    updated = 0
    for order in queryset:
        if order.status == 'processing':
            order.mark_as_shipped()
            updated += 1
    
    if updated > 0:
        modeladmin.message_user(request, f"Successfully marked {updated} order(s) as shipped.")
    else:
        modeladmin.message_user(request, "No orders were updated. Only processing orders can be marked as shipped.", level='WARNING')

mark_orders_as_shipped.short_description = "Mark selected orders as shipped"


def mark_orders_as_delivered(modeladmin, request, queryset):
    """Admin action to mark orders as delivered"""
    updated = 0
    for order in queryset:
        if order.status == 'shipped':
            order.mark_as_delivered()
            updated += 1
    
    if updated > 0:
        modeladmin.message_user(request, f"Successfully marked {updated} order(s) as delivered.")
    else:
        modeladmin.message_user(request, "No orders were updated. Only shipped orders can be marked as delivered.", level='WARNING')

mark_orders_as_delivered.short_description = "Mark selected orders as delivered"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'full_name', 'status', 'total_amount', 'wallet_amount_used', 'remaining_amount', 'is_returned', 'delivery_date', 'created_at')
    list_filter = ('status', 'delivery_date', 'created_at', 'payment_method', 'is_returned')
    search_fields = ('id', 'user__username', 'full_name', 'phone', 'tracking_number')
    readonly_fields = ('created_at', 'updated_at', 'shipped_at', 'delivered_at')
    inlines = [OrderItemInline]
    actions = [approve_upi_orders, process_order_return, mark_orders_as_shipped, mark_orders_as_delivered]

    fieldsets = (
        ('Customer', {
            'fields': ('user', 'session_key', 'full_name', 'phone')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code')
        }),
        ('Payment & Delivery', {
            'fields': ('payment_method', 'upi_provider', 'total_amount', 'wallet_amount_used', 'remaining_amount', 'delivery_date')
        }),
        ('Order Status & Tracking', {
            'fields': ('status', 'tracking_number', 'shipped_at', 'delivered_at')
        }),
        ('Return Information', {
            'fields': ('is_returned', 'return_reason', 'returned_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'unit_price', 'quantity', 'line_total')
    search_fields = ('order__id', 'product_name')


@admin.register(UPIPaymentMethod)
class UPIPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'upi_id', 'is_active', 'display_order')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'upi_id')
    list_editable = ('is_active', 'display_order')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'upi_id')
        }),
        ('Media', {
            'fields': ('logo', 'qr_code')
        }),
        ('Settings', {
            'fields': ('is_active', 'display_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
