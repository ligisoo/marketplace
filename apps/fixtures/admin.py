from django.contrib import admin
from .models import League, Team, Venue, Fixture, APIUsageLog


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'season', 'round']
    list_filter = ['country', 'season']
    search_fields = ['name', 'country']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'api_id']
    search_fields = ['name']


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'api_id']
    search_fields = ['name', 'city']


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ['home_team', 'away_team', 'date', 'status_short', 'home_goals', 'away_goals', 'league']
    list_filter = ['status_short', 'date', 'league']
    search_fields = ['home_team__name', 'away_team__name', 'league__name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'timestamp', 'date', 'response_cached']
    list_filter = ['endpoint', 'date', 'response_cached']
    readonly_fields = ['endpoint', 'date', 'timestamp', 'request_params', 'response_cached']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
