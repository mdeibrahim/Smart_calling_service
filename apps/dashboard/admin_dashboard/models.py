from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class AdminCampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"


class AdminCampaign(models.Model):
    """Admin Campaign model for global campaign management"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Campaign Name")
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(
        max_length=20, 
        choices=AdminCampaignStatus.choices, 
        default=AdminCampaignStatus.DRAFT,
        verbose_name="Status"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_campaigns",
        verbose_name="Created By"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    target_calls = models.IntegerField(default=0, verbose_name="Target Calls")
    priority = models.IntegerField(default=1, verbose_name="Priority")
    is_global = models.BooleanField(default=False, verbose_name="Global Campaign")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Admin Campaign"
        verbose_name_plural = "Admin Campaigns"

    def __str__(self):
        return f"{self.name} ({self.status})"


class AdminTarget(models.Model):
    """Admin Target model for setting targets across the organization"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_targets",
        verbose_name="User"
    )
    campaign = models.ForeignKey(
        'AdminCampaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="targets",
        verbose_name="Campaign"
    )
    target_calls = models.IntegerField(default=0, verbose_name="Target Calls")
    achieved_calls = models.IntegerField(default=0, verbose_name="Achieved Calls")
    target_revenue = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Target Revenue"
    )
    achieved_revenue = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Achieved Revenue"
    )
    period_start = models.DateField(verbose_name="Period Start")
    period_end = models.DateField(verbose_name="Period End")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_admin_targets",
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_end"]
        verbose_name = "Admin Target"
        verbose_name_plural = "Admin Targets"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'period_start', 'period_end'],
                name='unique_admin_user_period'
            )
        ]

    def clean(self):
        if self.period_end and self.period_start:
            if self.period_end < self.period_start:
                raise ValidationError("period_end must be after period_start")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Admin Target for {self.user.name or self.user.email} - {self.period_start} to {self.period_end}"

    @property
    def call_progress(self):
        if self.target_calls > 0:
            return (self.achieved_calls / self.target_calls) * 100
        return 0

    @property
    def revenue_progress(self):
        if self.target_revenue > 0:
            return (self.achieved_revenue / self.target_revenue) * 100
        return 0


class SystemSettings(models.Model):
    """System-wide settings managed by admin"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True, verbose_name="Setting Key")
    value = models.TextField(verbose_name="Setting Value")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_settings",
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class AuditLog(models.Model):
    """Audit log for tracking all admin actions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_audit_logs",
        verbose_name="User"
    )
    action = models.CharField(max_length=100, verbose_name="Action")
    model_name = models.CharField(max_length=100, verbose_name="Model Name")
    object_id = models.CharField(max_length=100, blank=True, verbose_name="Object ID")
    changes = models.JSONField(default=dict, blank=True, verbose_name="Changes")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} on {self.model_name} at {self.created_at}"
