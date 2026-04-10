from django.contrib import admin
from .models import ManagerCampaign, ManagerTarget


@admin.register(ManagerCampaign)
class ManagerCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'start_date', 'end_date', 'target_calls', 'created_at']
    list_filter = ['status', 'created_at', 'start_date']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ManagerTarget)
class ManagerTargetAdmin(admin.ModelAdmin):
    list_display = ['agent', 'campaign', 'target_calls', 'achieved_calls', 'target_revenue', 'achieved_revenue', 'period_start', 'period_end', 'created_by']
    list_filter = ['period_start', 'period_end', 'campaign']
    search_fields = ['agent__name', 'agent__email', 'campaign__name']
    date_hierarchy = 'period_start'
    ordering = ['-period_end']
    readonly_fields = ['id', 'created_at', 'updated_at']
