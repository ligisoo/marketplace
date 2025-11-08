from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from .models import Tip, TipMatch, TipPurchase, TipView, OCRProviderSettings, TipsterPayment


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


@admin.register(TipsterPayment)
class TipsterPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'tipster_name',
        'period_display',
        'total_revenue',
        'tipster_share',
        'platform_amount_display',
        'tips_count',
        'purchases_count',
        'status',
        'payment_method',
        'paid_at'
    )
    list_filter = ('status', 'payment_method', 'created_at', 'paid_at')
    search_fields = (
        'tipster__username',
        'tipster__phone_number',
        'tipster__userprofile__display_name',
        'transaction_reference'
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'platform_amount_display',
        'tipster_name'
    )
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Tipster Information', {
            'fields': ('tipster', 'tipster_name')
        }),
        ('Payment Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Financial Details', {
            'fields': (
                'total_revenue',
                'platform_commission',
                'tipster_share',
                'platform_amount_display',
                'tips_count',
                'purchases_count'
            )
        }),
        ('Payment Information', {
            'fields': (
                'status',
                'payment_method',
                'transaction_reference',
                'phone_number',
                'notes'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'processed_by'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'generate_payment_schedule',
        'export_payment_report_csv',
        'export_payment_report_excel',
        'mark_as_processing',
        'mark_as_completed',
        'mark_as_pending'
    ]

    def tipster_name(self, obj):
        """Display tipster's name"""
        return obj.tipster.userprofile.display_name
    tipster_name.short_description = 'Tipster Name'

    def period_display(self, obj):
        """Display payment period"""
        return f"{obj.period_start.strftime('%Y-%m-%d')} to {obj.period_end.strftime('%Y-%m-%d')}"
    period_display.short_description = 'Period'

    def platform_amount_display(self, obj):
        """Display platform's commission amount"""
        return f"KES {obj.platform_amount:,.2f}"
    platform_amount_display.short_description = 'Platform Share (40%)'

    def generate_payment_schedule(self, request, queryset):
        """Generate payment schedule for selected period"""
        # This action helps create new payment records
        self.message_user(
            request,
            f'Selected {queryset.count()} payment records. Use export actions to download.'
        )
    generate_payment_schedule.short_description = 'View selected payment schedule'

    def export_payment_report_csv(self, request, queryset):
        """Export payment report as CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tipster_payments_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        # Header
        writer.writerow([
            'Tipster Name',
            'Phone Number',
            'Period Start',
            'Period End',
            'Total Revenue (KES)',
            'Platform Commission (%)',
            'Platform Amount (KES)',
            'Tipster Share (KES)',
            'Tips Sold',
            'Total Purchases',
            'Status',
            'Payment Method',
            'Transaction Reference',
            'M-Pesa Phone',
            'Paid Date',
            'Notes'
        ])

        # Data rows
        for payment in queryset.select_related('tipster', 'tipster__userprofile'):
            writer.writerow([
                payment.tipster.userprofile.display_name,
                payment.tipster.phone_number,
                payment.period_start.strftime('%Y-%m-%d %H:%M'),
                payment.period_end.strftime('%Y-%m-%d %H:%M'),
                f'{payment.total_revenue:.2f}',
                f'{payment.platform_commission:.2f}',
                f'{payment.platform_amount:.2f}',
                f'{payment.tipster_share:.2f}',
                payment.tips_count,
                payment.purchases_count,
                payment.get_status_display(),
                payment.get_payment_method_display() if payment.payment_method else '',
                payment.transaction_reference,
                payment.phone_number,
                payment.paid_at.strftime('%Y-%m-%d %H:%M') if payment.paid_at else '',
                payment.notes
            ])

        self.message_user(request, f'Successfully exported {queryset.count()} payment records to CSV.')
        return response

    export_payment_report_csv.short_description = 'Export to CSV (Downloadable)'

    def export_payment_report_excel(self, request, queryset):
        """Export payment report as Excel-compatible CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tipster_payments_excel_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        # Header with summary
        writer.writerow(['LIGISOO TIPSTER PAYMENT SCHEDULE'])
        writer.writerow([f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([f'Total Records: {queryset.count()}'])
        writer.writerow([])

        # Calculate totals
        totals = queryset.aggregate(
            total_revenue=Sum('total_revenue'),
            total_tipster_share=Sum('tipster_share'),
            total_tips=Sum('tips_count'),
            total_purchases=Sum('purchases_count')
        )

        writer.writerow(['SUMMARY'])
        writer.writerow(['Total Revenue:', f'KES {totals["total_revenue"] or 0:,.2f}'])
        writer.writerow(['Total Tipster Payments:', f'KES {totals["total_tipster_share"] or 0:,.2f}'])
        writer.writerow(['Total Platform Commission:', f'KES {(totals["total_revenue"] or 0) - (totals["total_tipster_share"] or 0):,.2f}'])
        writer.writerow(['Total Tips Sold:', totals["total_tips"] or 0])
        writer.writerow(['Total Purchases:', totals["total_purchases"] or 0])
        writer.writerow([])

        # Detailed records header
        writer.writerow([
            'Tipster Name',
            'Phone Number',
            'Period Start',
            'Period End',
            'Total Revenue (KES)',
            'Platform Share (KES)',
            'Tipster Share (KES)',
            'Tips Sold',
            'Purchases',
            'Status',
            'Payment Method',
            'Transaction Ref',
            'M-Pesa Phone',
            'Paid Date',
            'Notes'
        ])

        # Data rows
        for payment in queryset.select_related('tipster', 'tipster__userprofile').order_by('-tipster_share'):
            writer.writerow([
                payment.tipster.userprofile.display_name,
                payment.tipster.phone_number,
                payment.period_start.strftime('%Y-%m-%d'),
                payment.period_end.strftime('%Y-%m-%d'),
                f'{payment.total_revenue:.2f}',
                f'{payment.platform_amount:.2f}',
                f'{payment.tipster_share:.2f}',
                payment.tips_count,
                payment.purchases_count,
                payment.get_status_display(),
                payment.get_payment_method_display() if payment.payment_method else '',
                payment.transaction_reference,
                payment.phone_number,
                payment.paid_at.strftime('%Y-%m-%d') if payment.paid_at else '',
                payment.notes.replace('\n', ' ').replace('\r', ' ')
            ])

        self.message_user(
            request,
            f'Successfully exported {queryset.count()} payment records with summary. Total to pay: KES {totals["total_tipster_share"] or 0:,.2f}'
        )
        return response

    export_payment_report_excel.short_description = 'Export Detailed Report with Summary (CSV)'

    def mark_as_processing(self, request, queryset):
        """Mark selected payments as processing"""
        updated = queryset.filter(status='pending').update(
            status='processing',
            processed_by=request.user
        )
        self.message_user(request, f'{updated} payment(s) marked as processing.')
    mark_as_processing.short_description = 'Mark as Processing'

    def mark_as_completed(self, request, queryset):
        """Mark selected payments as completed"""
        updated = queryset.filter(
            Q(status='pending') | Q(status='processing')
        ).update(
            status='completed',
            paid_at=timezone.now(),
            processed_by=request.user
        )
        self.message_user(request, f'{updated} payment(s) marked as completed.')
    mark_as_completed.short_description = 'Mark as Completed (Paid)'

    def mark_as_pending(self, request, queryset):
        """Mark selected payments back to pending"""
        updated = queryset.update(status='pending', paid_at=None)
        self.message_user(request, f'{updated} payment(s) marked as pending.')
    mark_as_pending.short_description = 'Mark as Pending'

    def save_model(self, request, obj, form, change):
        """Auto-set processed_by when saving"""
        if not change:  # Only on creation
            obj.processed_by = request.user
        super().save_model(request, obj, form, change)
