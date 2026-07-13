from django.contrib import admin
from .models import SubscriptionPayment


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'amount', 'status', 'phone_number', 'mpesa_receipt_number', 'created_at')
    list_filter = ('status', 'tier', 'created_at')
    search_fields = ('user__phone_number', 'mpesa_receipt_number', 'checkout_request_id')
    readonly_fields = ('checkout_request_id', 'merchant_request_id', 'callback_data', 'created_at', 'updated_at', 'completed_at')
    ordering = ['-created_at']
