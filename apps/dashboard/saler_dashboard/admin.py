from django.contrib import admin
from .models import Campaign, Contact, Lead, Target, CalibrationAudio, CalibrationSession, CalibrationAttempt, ReferenceText


class SafeAdminLogMixin:
    """Avoid hard 500s when legacy django_admin_log FK mismatches the active user model."""

    def log_addition(self, request, obj, message):
        return

    def log_change(self, request, obj, message):
        return

    def log_deletions(self, request, queryset):
        return


@admin.register(Campaign)
class CampaignAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'start_date', 'end_date', 'target_calls', 'created_at']
    list_filter = ['status', 'created_at', 'start_date']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Campaign Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Campaign Details', {
            'fields': ('start_date', 'end_date', 'target_calls')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Contact)
class ContactAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'email', 'company', 'created_by', 'created_at']
    list_filter = ['created_at', 'company']
    search_fields = ['name', 'phone_number', 'email', 'company']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'phone_number', 'email', 'company')
        }),
        ('Additional Details', {
            'fields': ('address', 'notes')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Lead)
class LeadAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display = ['id', 'contact', 'campaign', 'assigned_to', 'status', 'value', 'created_at']
    list_filter = ['status', 'created_at', 'campaign']
    search_fields = ['contact__name', 'contact__phone_number', 'assigned_to__name']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['contact', 'campaign', 'assigned_to']
    fieldsets = (
        ('Lead Information', {
            'fields': ('contact', 'campaign', 'status')
        }),
        ('Assignment and Value', {
            'fields': ('assigned_to', 'value', 'notes')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Target)
class TargetAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display = ['user', 'campaign', 'target_calls', 'achieved_calls', 'target_revenue', 'achieved_revenue', 'period_start', 'period_end']
    list_filter = ['period_start', 'period_end', 'campaign']
    search_fields = ['user__name', 'campaign__name']
    date_hierarchy = 'period_start'
    ordering = ['-period_end']
    readonly_fields = ['id', 'created_at', 'updated_at', 'call_progress', 'revenue_progress']
    raw_id_fields = ['user', 'campaign']
    fieldsets = (
        ('Target Assignment', {
            'fields': ('user', 'campaign', 'period_start', 'period_end')
        }),
        ('Call Targets', {
            'fields': ('target_calls', 'achieved_calls', 'call_progress')
        }),
        ('Revenue Targets', {
            'fields': ('target_revenue', 'achieved_revenue', 'revenue_progress')
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ─────────────────────────────────────────────
#        CALIBRATION ADMIN
# ─────────────────────────────────────────────

class ReferenceTextInline(admin.TabularInline):
    model = ReferenceText
    extra = 1
    fields = ['text_defficulty', 'reference_text']


@admin.register(CalibrationAudio)
class CalibrationAudioAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display       = ['order', 'title', 'is_active', 'created_at']
    list_display_links = ['title']          # 'title' is the clickable link
    list_editable      = ['is_active', 'order']
    list_filter        = ['is_active']
    search_fields      = ['title', 'description']
    ordering           = ['order']
    inlines            = [ReferenceTextInline]
    fieldsets = (
        ('Audio Info', {
            'fields': ('order', 'title', 'description', 'is_active')
        }),
        ('Files', {
            'description': 'Upload the audio file.',
            'fields': ('audio_file',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['created_at', 'updated_at']


class CalibrationAttemptInline(admin.TabularInline):
    model  = CalibrationAttempt
    extra  = 0
    fields = [
        'audio', 'recording_file', 'overall_score',
        'accuracy_score', 'fluency_score', 'confidence_score', 'is_analyzed',
    ]
    readonly_fields = [
        'overall_score', 'accuracy_score', 'fluency_score',
        'confidence_score', 'is_analyzed',
    ]
    can_delete = False


@admin.register(CalibrationSession)
class CalibrationSessionAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display  = ['id', 'seller', 'is_completed', 'overall_score', 'started_at', 'completed_at']
    list_filter   = ['is_completed', 'started_at']
    search_fields = ['seller__name', 'seller__email']
    ordering      = ['-started_at']
    readonly_fields = ['started_at', 'completed_at', 'overall_score', 'is_completed']
    inlines       = [CalibrationAttemptInline]


@admin.register(CalibrationAttempt)
class CalibrationAttemptAdmin(SafeAdminLogMixin, admin.ModelAdmin):
    list_display  = ['id', 'session', 'audio', 'overall_score', 'is_analyzed', 'created_at']
    list_filter   = ['is_analyzed', 'audio']
    search_fields = ['session__seller__name']
    ordering      = ['-created_at']
    readonly_fields = [
        'transcribed_text', 'accuracy_score', 'fluency_score',
        'confidence_score', 'overall_score', 'ai_feedback', 'is_analyzed', 'created_at',
    ]
    fieldsets = (
        ('Attempt', {
            'fields': ('session', 'audio', 'reference_text', 'recording_file')
        }),
        ('AI Analysis', {
            'fields': (
                'is_analyzed', 'transcribed_text',
                'overall_score', 'accuracy_score', 'fluency_score', 'confidence_score',
                'ai_feedback',
            ),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
