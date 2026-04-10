from django.db import models
from django.conf import settings
import uuid


class AuditorSettings(models.Model):
    """Auditor settings and preferences"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auditor_settings',
        verbose_name="Auditor"
    )
    default_page_size = models.IntegerField(default=20, verbose_name="Default Page Size")
    show_transcripts = models.BooleanField(default=True, verbose_name="Show Call Transcripts")
    show_reports = models.BooleanField(default=True, verbose_name="Show AI Reports")
    email_notifications = models.BooleanField(default=False, verbose_name="Email Notifications")
    notification_email = models.EmailField(blank=True, verbose_name="Notification Email")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Auditor Settings"
        verbose_name_plural = "Auditor Settings"

    def __str__(self):
        return f"Settings for {self.user.name or self.user.email}"


class AuditorFilterPreset(models.Model):
    """Saved filter presets for auditor"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auditor_filter_presets',
        verbose_name="Auditor"
    )
    name = models.CharField(max_length=100, verbose_name="Preset Name")
    filter_data = models.JSONField(default=dict, verbose_name="Filter Data")
    is_default = models.BooleanField(default=False, verbose_name="Default Preset")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Auditor Filter Preset"
        verbose_name_plural = "Auditor Filter Presets"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.user.name or self.user.email}"


class AuditorBookmark(models.Model):
    """Bookmarked calls for quick access"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auditor_bookmarks',
        verbose_name="Auditor"
    )
    call_id = models.IntegerField(verbose_name="Call ID")
    note = models.TextField(blank=True, verbose_name="Note")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditor Bookmark"
        verbose_name_plural = "Auditor Bookmarks"
        ordering = ["-created_at"]
        unique_together = [['user', 'call_id']]

    def __str__(self):
        return f"Bookmark {self.call_id} - {self.user.name or self.user.email}"
