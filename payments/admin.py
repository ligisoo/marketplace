from django.contrib import admin
from .models import TipPayment


@admin.register(TipPayment)
class TipPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tip', 'amount', 'status', 'phone_number', 'mpesa_receipt_number', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__phone_number', 'tip__bet_code', 'mpesa_receipt_number', 'checkout_request_id')
    readonly_fields = ('checkout_request_id', 'merchant_request_id', 'callback_data', 'created_at', 'updated_at')
    ordering = ['-created_at']
