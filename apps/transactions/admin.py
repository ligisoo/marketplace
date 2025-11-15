from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Account, Transaction, AccountingEntry
from .services import AccountingService


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'get_balance_display', 'user_link', 'is_active', 'created_at']
    list_filter = ['account_type', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'description', 'user__phone_number', 'user__username']
    readonly_fields = ['code', 'created_at', 'updated_at', 'get_balance_display', 'get_statement_link']

    fieldsets = (
        ('Account Information', {
            'fields': ('code', 'name', 'account_type', 'description')
        }),
        ('User Association', {
            'fields': ('user',),
            'description': 'Link to user for wallet accounts. Leave blank for GL accounts.'
        }),
        ('Balance & Status', {
            'fields': ('get_balance_display', 'is_active')
        }),
        ('Statement', {
            'fields': ('get_statement_link',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_balance_display(self, obj):
        balance = obj.get_balance()
        color = 'green' if balance >= 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">KES {:,.2f}</span>',
            color, balance
        )
    get_balance_display.short_description = 'Current Balance'

    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.phone_number)
        return '-'
    user_link.short_description = 'User'

    def get_statement_link(self, obj):
        # This could link to a custom admin view for statements
        return format_html(
            '<a href="#" onclick="alert(\'Statement view coming soon\')">View Statement</a>'
        )
    get_statement_link.short_description = 'Account Statement'


class AccountingEntryInline(admin.TabularInline):
    model = AccountingEntry
    extra = 0
    readonly_fields = ['entry_type', 'account', 'amount', 'description', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'transaction_type', 'user_link', 'amount_display', 'is_void', 'created_at']
    list_filter = ['transaction_type', 'is_void', 'created_at']
    search_fields = ['reference', 'description', 'user__phone_number', 'user__username']
    readonly_fields = ['reference', 'transaction_type', 'description', 'user', 'amount',
                       'metadata', 'created_at', 'created_by', 'get_entries_display',
                       'get_balance_check']
    inlines = [AccountingEntryInline]

    fieldsets = (
        ('Transaction Information', {
            'fields': ('reference', 'transaction_type', 'description', 'user', 'amount')
        }),
        ('Entries', {
            'fields': ('get_entries_display', 'get_balance_check')
        }),
        ('Status', {
            'fields': ('is_void', 'void_reason', 'voided_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.phone_number)
    user_link.short_description = 'User'

    def amount_display(self, obj):
        return format_html('<strong>KES {:,.2f}</strong>', obj.amount)
    amount_display.short_description = 'Amount'

    def get_entries_display(self, obj):
        if not obj.pk:
            return '-'

        entries = obj.entries.all()
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f5f5f5;"><th>Account</th><th>Debit</th><th>Credit</th><th>Description</th></tr>'

        for entry in entries:
            debit = f'KES {entry.amount:,.2f}' if entry.entry_type == 'debit' else '-'
            credit = f'KES {entry.amount:,.2f}' if entry.entry_type == 'credit' else '-'
            html += f'<tr><td>{entry.account.code}</td><td>{debit}</td><td>{credit}</td><td>{entry.description}</td></tr>'

        html += '</table>'
        return mark_safe(html)
    get_entries_display.short_description = 'Accounting Entries'

    def get_balance_check(self, obj):
        if not obj.pk:
            return '-'

        from decimal import Decimal
        debits = obj.entries.filter(entry_type='debit', is_void=False).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        credits = obj.entries.filter(entry_type='credit', is_void=False).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')

        balanced = debits == credits
        color = 'green' if balanced else 'red'
        icon = '✓' if balanced else '✗'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} Debits: KES {:,.2f} | Credits: KES {:,.2f}</span>',
            color, icon, debits, credits
        )
    get_balance_check.short_description = 'Balance Check'

    def has_add_permission(self, request):
        # Prevent manual creation of transactions
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of transactions
        return False


@admin.register(AccountingEntry)
class AccountingEntryAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'transaction_link', 'account_link', 'entry_type', 'amount_display', 'description']
    list_filter = ['entry_type', 'is_void', 'created_at', 'account__account_type']
    search_fields = ['description', 'transaction__reference', 'account__code', 'account__name']
    readonly_fields = ['transaction', 'entry_type', 'account', 'amount', 'description', 'is_void', 'created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Entry Information', {
            'fields': ('transaction', 'entry_type', 'account', 'amount', 'description')
        }),
        ('Status', {
            'fields': ('is_void',)
        }),
        ('Audit', {
            'fields': ('created_at',)
        }),
    )

    def transaction_link(self, obj):
        url = reverse('admin:transactions_transaction_change', args=[obj.transaction.id])
        return format_html('<a href="{}">{}</a>', url, obj.transaction.reference)
    transaction_link.short_description = 'Transaction'

    def account_link(self, obj):
        url = reverse('admin:transactions_account_change', args=[obj.account.id])
        return format_html('<a href="{}">{}</a>', url, obj.account.code)
    account_link.short_description = 'Account'

    def amount_display(self, obj):
        color = 'green' if obj.entry_type == 'debit' else 'blue'
        return format_html(
            '<span style="color: {}; font-weight: bold;">KES {:,.2f}</span>',
            color, obj.amount
        )
    amount_display.short_description = 'Amount'

    def has_add_permission(self, request):
        # Prevent manual creation of entries
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of entries
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent modification of entries
        return False


# Add custom admin actions
@admin.action(description='View GL Statement')
def view_gl_statement(modeladmin, request, queryset):
    # This would redirect to a custom view for GL statements
    pass


@admin.action(description='Sync Wallet Balance')
def sync_wallet_balance(modeladmin, request, queryset):
    from django.contrib import messages
    synced_count = 0

    for account in queryset:
        if account.user:
            AccountingService.sync_wallet_balance(account.user)
            synced_count += 1

    messages.success(request, f'Synced {synced_count} wallet balance(s)')


AccountAdmin.actions = [view_gl_statement, sync_wallet_balance]


# Fix import for Sum
from django.db import models
