from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class ManagerCampaign(models.Model):
    """Manager Campaign model for managing calling campaigns at manager level"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Campaign Name")
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(
        max_length=20, 
        choices=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("paused", "Paused"),
            ("completed", "Completed"),
        ], 
        default="draft",
        verbose_name="Status"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manager_campaigns",
        verbose_name="Created By"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    target_calls = models.IntegerField(default=0, verbose_name="Target Calls")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Manager Campaign"
        verbose_name_plural = "Manager Campaigns"

    def __str__(self):
        return f"{self.name} ({self.status})"


class ManagerTarget(models.Model):
    """Manager Target model for setting targets for agents"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="manager_targets",
        verbose_name="Agent"
    )
    campaign = models.ForeignKey(
        'ManagerCampaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_targets",
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
        related_name="created_targets",
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_end"]
        verbose_name = "Manager Target"
        verbose_name_plural = "Manager Targets"
        constraints = [
            models.UniqueConstraint(
                fields=['agent', 'period_start', 'period_end'],
                name='unique_agent_period'
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
        return f"Target for {self.agent.name or self.agent.email} - {self.period_start} to {self.period_end}"

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
