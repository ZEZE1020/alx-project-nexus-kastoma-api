from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem, Coupon, CouponUsage


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at', 'payment_method')
    search_fields = ('order_number', 'customer_email', 'user__email')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'item_count')
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'item_count', 'created_at', 'updated_at')
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'customer_phone')
        }),
        ('Billing Address', {
            'fields': ('billing_first_name', 'billing_last_name', 'billing_company',
                      'billing_address_line1', 'billing_address_line2', 'billing_city',
                      'billing_state', 'billing_postal_code', 'billing_country')
        }),
        ('Shipping Address', {
            'fields': ('shipping_first_name', 'shipping_last_name', 'shipping_company',
                      'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
                      'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'payment_reference')
        }),
        ('Shipping Information', {
            'fields': ('shipping_method', 'tracking_number', 'tracking_carrier', 'tracking_url', 'estimated_delivery_date')
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes')
        }),
        ('Timestamps', {
            'fields': ('confirmed_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'order', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status', 'created_at')
    search_fields = ('product_name', 'product_sku', 'order__order_number')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'total_amount', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('item_count', 'total_amount')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'cart', 'quantity', 'subtotal')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'cart__user__email')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'discount_type', 'discount_value', 'usage_count', 'is_active', 'valid_from', 'valid_until')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('code', 'name')
    readonly_fields = ('usage_count',)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'order', 'user', 'discount_amount', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('coupon__code', 'order__order_number', 'user__email')
