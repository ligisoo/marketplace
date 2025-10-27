from django.contrib import admin
from .models import Tip, TipMatch, TipPurchase, TipView


class TipMatchInline(admin.TabularInline):
    model = TipMatch
    extra = 0
    readonly_fields = ('is_resulted', 'is_won', 'actual_result')


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ('bet_code', 'tipster', 'bookmaker', 'odds', 'price', 'status', 'purchase_count_display', 'created_at')
    list_filter = ('status', 'bookmaker', 'is_resulted', 'is_won', 'created_at')
    search_fields = ('bet_code', 'tipster__username', 'tipster__phone_number')
    readonly_fields = ('created_at', 'updated_at', 'ocr_confidence', 'match_details', 'preview_data')
    inlines = [TipMatchInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tipster', 'bet_code', 'bookmaker', 'odds', 'price', 'status')
        }),
        ('Media & OCR', {
            'fields': ('screenshot', 'ocr_processed', 'ocr_confidence', 'match_details', 'preview_data'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('expires_at', 'created_at', 'updated_at')
        }),
        ('Results', {
            'fields': ('is_resulted', 'is_won', 'result_verified_at')
        }),
    )
    
    def purchase_count_display(self, obj):
        return obj.purchases.filter(status='completed').count()
    purchase_count_display.short_description = 'Purchases'
    
    actions = ['approve_tips', 'reject_tips']
    
    def approve_tips(self, request, queryset):
        updated = queryset.filter(status='pending_approval').update(status='active')
        self.message_user(request, f'{updated} tips approved successfully.')
    approve_tips.short_description = 'Approve selected tips'
    
    def reject_tips(self, request, queryset):
        updated = queryset.filter(status='pending_approval').update(status='rejected')
        self.message_user(request, f'{updated} tips rejected.')
    reject_tips.short_description = 'Reject selected tips'


@admin.register(TipMatch)
class TipMatchAdmin(admin.ModelAdmin):
    list_display = ('tip', 'home_team', 'away_team', 'market', 'odds', 'match_date', 'is_resulted', 'is_won')
    list_filter = ('is_resulted', 'is_won', 'match_date', 'market')
    search_fields = ('home_team', 'away_team', 'league', 'tip__bet_code')
    readonly_fields = ('tip',)


@admin.register(TipPurchase)
class TipPurchaseAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'tip', 'buyer', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('transaction_id', 'tip__bet_code', 'buyer__username', 'buyer__phone_number')
    readonly_fields = ('transaction_id', 'created_at', 'completed_at')


@admin.register(TipView)
class TipViewAdmin(admin.ModelAdmin):
    list_display = ('tip', 'user', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('tip__bet_code', 'user__username', 'ip_address')
    readonly_fields = ('tip', 'user', 'ip_address', 'user_agent', 'viewed_at')
