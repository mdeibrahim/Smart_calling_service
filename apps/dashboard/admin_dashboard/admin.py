from django.contrib import admin
from .models import AdminCampaign, AdminTarget, SystemSettings, AuditLog


@admin.register(AdminCampaign)
class AdminCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'start_date', 'end_date', 'target_calls', 'is_global', 'created_at']
    list_filter = ['status', 'is_global', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'description', 'status', 'priority', 'is_global')
        }),
        ('Campaign Details', {
            'fields': ('start_date', 'end_date', 'target_calls')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AdminTarget)
class AdminTargetAdmin(admin.ModelAdmin):
    list_display = ['user', 'campaign', 'target_calls', 'achieved_calls', 'call_progress', 'period_start', 'period_end', 'created_at']
    list_filter = ['period_start', 'period_end', 'created_at']
    search_fields = ['user__name', 'user__email', 'campaign__name']
    readonly_fields = ['id', 'call_progress', 'revenue_progress', 'created_at', 'updated_at']
    ordering = ['-period_end']
    
    fieldsets = (
        ('Target Information', {
            'fields': ('user', 'campaign', 'period_start', 'period_end')
        }),
        ('Call Targets', {
            'fields': ('target_calls', 'achieved_calls', 'call_progress')
        }),
        ('Revenue Targets', {
            'fields': ('target_revenue', 'achieved_revenue', 'revenue_progress')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['key']
    
    fieldsets = (
        ('Setting', {
            'fields': ('key', 'value', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'ip_address', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    search_fields = ['user__name', 'user__email', 'action', 'model_name', 'object_id']
    readonly_fields = ['id', 'user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'user_agent', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Action Details', {
            'fields': ('user', 'action', 'model_name', 'object_id')
        }),
        ('Changes', {
            'fields': ('changes',),
            'classes': ('collapse',)
        }),
        ('Request Info', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
