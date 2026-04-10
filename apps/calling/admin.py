from django.contrib import admin
from .models import Call, CallTranscript, CallReport, AIResponse


class CallTranscriptInline(admin.TabularInline):
    model = CallTranscript
    extra = 0
    readonly_fields = [
        "role",
        "content",
        "timestamp",
        "ai_used_percentage",
        "created_at",
    ]
    can_delete = False
    fields = ["role", "timestamp", "content", "ai_used_percentage"]


class AIResponseInline(admin.TabularInline):
    model = AIResponse
    extra = 0
    readonly_fields = ["timestamp", "suggestion", "was_used", "created_at"]
    can_delete = False
    fields = ["timestamp", "suggestion", "was_used"]


class CallReportInline(admin.StackedInline):
    model = CallReport
    extra = 0
    readonly_fields = ["report_data", "performance_score", "call_status", "created_at"]
    can_delete = False


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "customer_number",
        "seller_number",
        "status",
        "duration_seconds",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["customer_number", "seller_number", "twilio_call_sid", "user__email"]
    readonly_fields = [
        "id",
        "twilio_call_sid",
        "started_at",
        "ended_at",
        "duration_seconds",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Call Information",
            {"fields": ("id", "user", "customer_number", "seller_number", "status")},
        ),
        ("Twilio Details", {"fields": ("twilio_call_sid",)}),
        (
            "Timing",
            {
                "fields": (
                    "started_at",
                    "ended_at",
                    "duration_seconds",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
    inlines = [CallTranscriptInline, AIResponseInline, CallReportInline]


@admin.register(CallTranscript)
class CallTranscriptAdmin(admin.ModelAdmin):
    list_display = ["call", "role", "timestamp", "content_preview", "created_at"]
    list_filter = ["role", "created_at"]
    search_fields = ["content", "call__id"]
    readonly_fields = [
        "call",
        "role",
        "content",
        "timestamp",
        "ai_used_percentage",
        "created_at",
    ]

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content Preview"


@admin.register(CallReport)
class CallReportAdmin(admin.ModelAdmin):
    list_display = ["call", "performance_score", "call_status", "created_at"]
    list_filter = ["call_status", "created_at"]
    search_fields = ["call__id"]
    readonly_fields = [
        "call",
        "report_data",
        "performance_score",
        "call_status",
        "created_at",
    ]


@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    list_display = ["call", "timestamp", "suggestion_preview", "was_used", "created_at"]
    list_filter = ["was_used", "created_at"]
    search_fields = ["suggestion", "call__id"]
    readonly_fields = [
        "call",
        "transcript",
        "suggestion",
        "timestamp",
        "was_used",
        "created_at",
    ]

    def suggestion_preview(self, obj):
        return (
            obj.suggestion[:100] + "..."
            if len(obj.suggestion) > 100
            else obj.suggestion
        )

    suggestion_preview.short_description = "Suggestion Preview"
