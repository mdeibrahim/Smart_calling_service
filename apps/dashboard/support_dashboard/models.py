from django.db import models
from django.conf import settings
import uuid


class TicketStatus(models.TextChoices):
    OPEN = "open", "Open"
    IN_PROGRESS = "in_progress", "In Progress"
    RESOLVED = "resolved", "Resolved"
    CLOSED = "closed", "Closed"


class TicketPriority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class SupportTicket(models.Model):
    """Support ticket model for tracking customer support requests"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True, verbose_name="Ticket Number")
    subject = models.CharField(max_length=200, verbose_name="Subject")
    description = models.TextField(verbose_name="Description")
    status = models.CharField(
        max_length=20, 
        choices=TicketStatus.choices, 
        default=TicketStatus.OPEN,
        verbose_name="Status"
    )
    priority = models.CharField(
        max_length=20, 
        choices=TicketPriority.choices, 
        default=TicketPriority.MEDIUM,
        verbose_name="Priority"
    )
    customer_name = models.CharField(max_length=100, verbose_name="Customer Name")
    customer_phone = models.CharField(max_length=20, verbose_name="Customer Phone")
    customer_email = models.EmailField(blank=True, verbose_name="Customer Email")
    
    # Related call (optional)
    related_call_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Related Call ID")
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Assigned To"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tickets",
        verbose_name="Created By"
    )
    
    resolution_notes = models.TextField(blank=True, verbose_name="Resolution Notes")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Resolved At")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


class TicketComment(models.Model):
    """Comments on support tickets"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        SupportTicket, 
        on_delete=models.CASCADE, 
        related_name="comments",
        verbose_name="Ticket"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_comments",
        verbose_name="User"
    )
    comment = models.TextField(verbose_name="Comment")
    is_internal = models.BooleanField(default=False, verbose_name="Internal Note")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Ticket Comment"
        verbose_name_plural = "Ticket Comments"

    def __str__(self):
        return f"Comment on {self.ticket.ticket_number} by {self.user.email}"
