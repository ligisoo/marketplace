from django.contrib import admin
from .models import AdminNotification


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ('level_icon', 'title', 'message_preview', 'related_tip', 'is_read', 'created_at')
    list_filter = ('level', 'is_read', 'created_at')
    list_editable = ('is_read',)
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_unread']
    
    def level_icon(self, obj):
        icons = {'info': 'ℹ️', 'warning': '⚠️', 'error': '🚨'}
        return f"{icons.get(obj.level, '•')} {obj.get_level_display()}"
    level_icon.short_description = 'Level'
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} notifications marked as read.')
    mark_as_read.short_description = '✓ Mark as read'
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} notifications marked as unread.')
    mark_as_unread.short_description = '✗ Mark as unread'
