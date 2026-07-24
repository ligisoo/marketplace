from django.contrib import admin
from .models import SubscriptionPayment, PromoCode, PromoCodeRedemption


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'amount', 'status', 'phone_number', 'mpesa_receipt_number', 'created_at')
    list_filter = ('status', 'tier', 'created_at')
    search_fields = ('user__phone_number', 'mpesa_receipt_number', 'checkout_request_id')
    readonly_fields = ('checkout_request_id', 'merchant_request_id', 'callback_data', 'created_at', 'updated_at', 'completed_at')
    ordering = ['-created_at']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'pro_duration_days', 'used_count', 'max_uses', 'is_active', 'expires_at', 'created_at')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('code',)
    readonly_fields = ('used_count', 'created_at', 'updated_at')
    ordering = ['-created_at']


@admin.register(PromoCodeRedemption)
class PromoCodeRedemptionAdmin(admin.ModelAdmin):
    list_display = ('promo_code', 'user', 'redeemed_at')
    list_filter = ('redeemed_at',)
    search_fields = ('promo_code__code', 'user__phone_number', 'user__username')
    readonly_fields = ('promo_code', 'user', 'redeemed_at')
    ordering = ['-redeemed_at']

    def has_add_permission(self, request):
        return False

