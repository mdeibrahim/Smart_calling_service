from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid


class CampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"


class Campaign(models.Model):
    """Campaign model for managing calling campaigns"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Campaign Name")
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(
        max_length=20, 
        choices=CampaignStatus.choices, 
        default=CampaignStatus.DRAFT,
        verbose_name="Status"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name="Created By"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")
    target_calls = models.IntegerField(default=0, verbose_name="Target Calls")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"

    def __str__(self):
        return f"{self.name} ({self.status})"


class LeadStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    INTERESTED = "interested", "Interested"
    NOT_INTERESTED = "not_interested", "Not Interested"
    FOLLOW_UP = "follow_up", "Follow Up"
    CONVERTED = "converted", "Converted"


class Contact(models.Model):
    """Contact model for managing customer contacts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Contact Name")
    phone_number = models.CharField(max_length=20, verbose_name="Phone Number")
    email = models.EmailField(blank=True, verbose_name="Email")
    company = models.CharField(max_length=200, blank=True, verbose_name="Company")
    address = models.TextField(blank=True, verbose_name="Address")
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

    def __str__(self):
        return f"{self.name} - {self.phone_number}"


class Lead(models.Model):
    """Lead model for tracking sales leads"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(
        Contact, 
        on_delete=models.CASCADE, 
        related_name="leads",
        verbose_name="Contact"
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
        verbose_name="Campaign"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_leads",
        verbose_name="Assigned To"
    )
    status = models.CharField(
        max_length=20,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
        verbose_name="Status"
    )
    value = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Lead Value"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Lead"
        verbose_name_plural = "Leads"

    def __str__(self):
        return f"Lead {self.id} - {self.contact.name} ({self.status})"


class Target(models.Model):
    """Target model for tracking sales targets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="targets",
        verbose_name="User"
    )
    campaign = models.ForeignKey(
        Campaign,
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_end"]
        verbose_name = "Target"
        verbose_name_plural = "Targets"

    def clean(self):
        if self.period_end and self.period_start:
            if self.period_end < self.period_start:
                raise ValidationError("period_end must be after period_start")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Target for {self.user.name} - {self.period_start} to {self.period_end}"

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


# ─────────────────────────────────────────────
#           CALIBRATION MODELS
# ─────────────────────────────────────────────

class CalibrationAudio(models.Model):
    """7 fixed audio files uploaded by admin for seller training."""

    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(blank=True, verbose_name="Description")
    audio_file = models.FileField(
        upload_to="calibration/audios/",
        verbose_name="Audio File",
        help_text="Upload MP3 / WAV audio file",
    )
    # reference_text = models.TextField(
    #     verbose_name="Reference Text",
    #     help_text="The text seller must read aloud after listening to this audio",
    # )
    order = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Display Order",
        help_text="Order 1-7",
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Calibration Audio"
        verbose_name_plural = "Calibration Audios"

    def __str__(self):
        return f"#{self.order} - {self.title}"

class ReferenceText(models.Model):
    """Reference text for calibration audios."""
    TEXT_CHOICES = (
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    )
    audio = models.ForeignKey(
        CalibrationAudio,
        on_delete=models.CASCADE,
        related_name="reference_texts",
        verbose_name="Calibration Audio",
    )
    text_defficulty = models.CharField(
        max_length=10,
        choices=TEXT_CHOICES,
        default="easy",
        verbose_name="Text Difficulty",
    )
    reference_text = models.TextField(
        verbose_name="Reference Text",
        help_text="The text seller must read aloud after listening to this audio",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["audio"]
        verbose_name = "Reference Text"
        verbose_name_plural = "Reference Texts"

    def __str__(self):
        return f"Reference Text for #{self.audio.order} - {self.audio.title}"


class CalibrationSession(models.Model):
    """One full training session by a seller (covers all 7 audios)."""

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calibration_sessions",
        verbose_name="Seller",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    overall_score = models.FloatField(
        null=True, blank=True,
        verbose_name="Overall Score",
        help_text="Average AI score across all attempts (0-100)",
    )

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Calibration Session"
        verbose_name_plural = "Calibration Sessions"

    def __str__(self):
        return f"Session #{self.id} - {self.seller} ({'Done' if self.is_completed else 'In Progress'})"


class CalibrationAttempt(models.Model):
    """Seller recording for a single audio within a session + AI result."""

    session = models.ForeignKey(
        CalibrationSession,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Session",
    )
    audio = models.ForeignKey(
        CalibrationAudio,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Calibration Audio",
    )
    reference_text = models.ForeignKey(
        ReferenceText,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
        verbose_name="Assigned Reference Text",
        help_text="The specific text the seller was asked to read",
    )
    recording_file = models.FileField(
        upload_to="calibration/recordings/",
        verbose_name="Seller Recording",
        help_text="Seller's voice recording for this audio",
    )
    # ── AI Results ──────────────────────────────────────────────────────────
    transcribed_text = models.TextField(
        blank=True,
        verbose_name="Transcribed Text",
        help_text="What Groq Whisper heard from the seller's recording",
    )
    accuracy_score = models.FloatField(
        null=True, blank=True,
        verbose_name="Accuracy Score (0-100)",
    )
    fluency_score = models.FloatField(
        null=True, blank=True,
        verbose_name="Fluency Score (0-100)",
    )
    confidence_score = models.FloatField(
        null=True, blank=True,
        verbose_name="Confidence Score (0-100)",
    )
    overall_score = models.FloatField(
        null=True, blank=True,
        verbose_name="Overall Score (0-100)",
    )
    ai_feedback = models.JSONField(
        null=True, blank=True,
        verbose_name="AI Detailed Feedback",
        help_text="Full JSON feedback from Groq LLaMA analysis",
    )
    is_analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = [("session", "audio")]  # one attempt per audio per session
        verbose_name = "Calibration Attempt"
        verbose_name_plural = "Calibration Attempts"

    def __str__(self):
        return f"Attempt - {self.session} | Audio #{self.audio.order} | Score: {self.overall_score}"
