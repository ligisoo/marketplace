from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('phone_number', 'username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'userprofile__is_buyer', 'userprofile__is_tipster', 'userprofile__is_verified')
    search_fields = ('phone_number', 'username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_user_roles', 'wallet_balance', 'is_verified', 'created_at')
    list_filter = ('is_buyer', 'is_tipster', 'is_verified', 'created_at')
    search_fields = ('user__phone_number', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

    def get_user_roles(self, obj):
        """Display user roles as a comma-separated string"""
        roles = []
        if obj.is_buyer:
            roles.append('Buyer')
        if obj.is_tipster:
            roles.append('Tipster')
        return ', '.join(roles) if roles else 'No roles'
    get_user_roles.short_description = 'User Roles'


admin.site.register(User, UserAdmin)
