import uuid
from django.db import models
from django.conf import settings


class CallStatus(models.TextChoices):
    INITIATED = "initiated", "Initiated"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class TranscriptRole(models.TextChoices):
    CALLER = "caller", "Caller"
    CALLEE = "callee", "Callee"


class Call(models.Model):
    """Main call record tracking the entire call session"""

    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="calls",
        help_text="User who initiated the call",
    )
    seller_number = models.CharField(max_length=20, help_text="Seller's phone number")
    customer_number = models.CharField(
        max_length=20, help_text="Customer's phone number"
    )
    twilio_call_sid = models.CharField(
        max_length=100, blank=True, null=True, help_text="Twilio Call SID"
    )
    status = models.CharField(
        max_length=20, choices=CallStatus.choices, default=CallStatus.INITIATED
    )
    started_at = models.DateTimeField(
        null=True, blank=True, help_text="When the call actually started"
    )
    ended_at = models.DateTimeField(
        null=True, blank=True, help_text="When the call ended"
    )
    duration_seconds = models.IntegerField(
        null=True, blank=True, help_text="Total call duration in seconds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["twilio_call_sid"]),
        ]

    def __str__(self):
        return f"Call {self.id} - {self.seller_number} to {self.customer_number} ({self.status})"


class CallTranscript(models.Model):
    """Individual conversation messages during the call"""

    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name="transcripts")
    role = models.CharField(max_length=10, choices=TranscriptRole.choices)
    content = models.TextField(help_text="Transcribed text")
    timestamp = models.CharField(max_length=10, help_text="Timestamp in MM:SS format")
    ai_used_percentage = models.FloatField(
        null=True, blank=True, help_text="Similarity score for caller messages (0-1)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["call", "created_at"]),
        ]

    def __str__(self):
        return f"{self.role} at {self.timestamp}: {self.content[:50]}"


class CallReport(models.Model):
    """AI-generated comprehensive analysis of the call"""

    call = models.OneToOneField(Call, on_delete=models.CASCADE, related_name="report")
    report_data = models.JSONField(help_text="Complete JSON report from LLM")
    performance_score = models.IntegerField(
        null=True, blank=True, help_text="Performance score out of 100"
    )
    call_status = models.CharField(
        max_length=50, blank=True, help_text="Success/In Progress/Needs Revisit"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Call {self.call.id} - Score: {self.performance_score}"


class AIResponse(models.Model):
    """AI suggestions sent to caller during the call"""

    call = models.ForeignKey(
        Call, on_delete=models.CASCADE, related_name="ai_responses"
    )
    transcript = models.ForeignKey(
        CallTranscript,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The callee message that triggered this suggestion",
    )
    suggestion = models.TextField(help_text="AI-generated response suggestion")
    timestamp = models.CharField(max_length=10, help_text="Timestamp in MM:SS format")
    was_used = models.BooleanField(
        default=False, help_text="Whether caller used this suggestion"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["call", "created_at"]),
        ]

    def __str__(self):
        return f"AI Suggestion at {self.timestamp}: {self.suggestion[:50]}"
