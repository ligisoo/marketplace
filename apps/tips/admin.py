from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from .models import Tip, TipMatch, OCRProviderSettings


class MissingApiMatchIdFilter(admin.SimpleListFilter):
    title = 'API Coverage'
    parameter_name = 'api_coverage'

    def lookups(self, request, model_admin):
        return (
            ('missing', 'Missing API ID'),
            ('has_id', 'Has API ID'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'missing':
            return queryset.filter(Q(api_match_id__isnull=True) | Q(api_match_id=''))
        if self.value() == 'has_id':
            return queryset.exclude(Q(api_match_id__isnull=True) | Q(api_match_id=''))
        return queryset


class TipMatchInline(admin.TabularInline):
    model = TipMatch
    extra = 0


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ('bet_code', 'tipster', 'bookmaker', 'odds', 'status', 'unresulted_matches', 'created_at')
    list_filter = ('status', 'bookmaker', 'is_resulted', 'is_won', 'created_at')
    search_fields = ('bet_code', 'tipster__username', 'tipster__phone_number')
    readonly_fields = ('created_at', 'updated_at', 'ocr_confidence', 'match_details', 'preview_data')
    inlines = [TipMatchInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('tipster', 'bet_code', 'bookmaker', 'odds', 'status')
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
    
    actions = ['approve_tips', 'reject_tips']
    
    def approve_tips(self, request, queryset):
        updated = queryset.filter(status='pending_approval').update(status='active')
        self.message_user(request, f'{updated} tips approved successfully.')
    approve_tips.short_description = 'Approve selected tips'
    
    def reject_tips(self, request, queryset):
        updated = queryset.filter(status='pending_approval').update(status='rejected')
        self.message_user(request, f'{updated} tips rejected.')
    reject_tips.short_description = 'Reject selected tips'

    def unresulted_matches(self, obj):
        return obj.matches.filter(is_resulted=False).count()
    unresulted_matches.short_description = 'Unresulted Matches'


@admin.register(TipMatch)
class TipMatchAdmin(admin.ModelAdmin):
    list_display = ('tip', 'home_team', 'away_team', 'market', 'odds', 'match_date', 'is_resulted', 'is_won', 'actual_result', 'api_match_id')
    list_editable = ('is_resulted', 'is_won', 'actual_result')
    list_filter = ('is_resulted', 'is_won', MissingApiMatchIdFilter, 'match_date', 'market')
    search_fields = ('home_team', 'away_team', 'league', 'tip__bet_code')
    readonly_fields = ('tip', 'api_match_id')
    actions = ['mark_as_won', 'mark_as_lost']

    def _recalculate_tip_result(self, tip):
        """Recalculate tip-level result when all matches are resulted"""
        matches = tip.matches.all()
        total = matches.count()
        resulted = matches.filter(is_resulted=True).count()
        
        if total > 0 and resulted == total:
            from decimal import Decimal
            all_won = not matches.filter(is_won=False).exists()
            
            tip.is_resulted = True
            tip.is_won = all_won
            tip.result_verified_at = timezone.now()
            tip.status = 'archived'
            
            # Recalculate odds
            total_odds = Decimal('1.00')
            for m in matches:
                total_odds *= m.odds
            tip.odds = round(total_odds, 2)
            
            tip.save()

    def mark_as_won(self, request, queryset):
        for match in queryset:
            match.is_resulted = True
            match.is_won = True
            match.actual_result = match.actual_result or 'Manually verified (Won)'
            match.save()
            self._recalculate_tip_result(match.tip)
        self.message_user(request, f'{queryset.count()} matches marked as WON.')
    mark_as_won.short_description = '✅ Mark selected matches as WON'

    def mark_as_lost(self, request, queryset):
        for match in queryset:
            match.is_resulted = True
            match.is_won = False
            match.actual_result = match.actual_result or 'Manually verified (Lost)'
            match.save()
            self._recalculate_tip_result(match.tip)
        self.message_user(request, f'{queryset.count()} matches marked as LOST.')
    mark_as_lost.short_description = '❌ Mark selected matches as LOST'


@admin.register(OCRProviderSettings)
class OCRProviderSettingsAdmin(admin.ModelAdmin):
    list_display = ('get_provider_display', 'updated_at', 'updated_by')
    readonly_fields = ('updated_at', 'updated_by')

    def has_add_permission(self, request):
        # Only allow adding if no settings exist
        return not OCRProviderSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion to ensure settings always exist
        return False

    def save_model(self, request, obj, form, change):
        # Set the user who updated the settings
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_provider_display(self, obj):
        return obj.get_provider_display()
    get_provider_display.short_description = 'Active OCR Provider'
