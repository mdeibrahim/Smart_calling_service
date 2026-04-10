from rest_framework import serializers
from apps.dashboard.support_dashboard.models import SupportTicket, TicketComment


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for Support Ticket model"""
    
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    ticket_status_display = serializers.CharField(source='get_status_display', read_only=True)
    ticket_priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'subject', 'description', 
            'status', 'status_display', 'ticket_status_display',
            'priority', 'priority_display', 'ticket_priority_display',
            'customer_name', 'customer_phone', 'customer_email',
            'related_call_id', 'assigned_to', 'assigned_to_name',
            'created_by', 'created_by_name', 'resolution_notes',
            'resolved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'created_at', 'updated_at']


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Support Tickets"""
    
    class Meta:
        model = SupportTicket
        fields = [
            'subject', 'description', 'priority',
            'customer_name', 'customer_phone', 'customer_email',
            'related_call_id'
        ]
    
    def create(self, validated_data):
        # Generate ticket number
        from django.utils import timezone
        from datetime import datetime
        
        today = timezone.now().date()
        count = SupportTicket.objects.filter(created_at__date=today).count() + 1
        ticket_number = f"SUP-{today.strftime('%Y%m%d')}-{count:04d}"
        
        validated_data['ticket_number'] = ticket_number
        validated_data['created_by'] = self.context['request'].user
        
        return super().create(validated_data)


class SupportTicketUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Support Tickets"""
    
    class Meta:
        model = SupportTicket
        fields = [
            'subject', 'description', 'status', 'priority',
            'customer_name', 'customer_phone', 'customer_email',
            'related_call_id', 'assigned_to', 'resolution_notes', 'resolved_at'
        ]


class TicketCommentSerializer(serializers.ModelSerializer):
    """Serializer for Ticket Comments"""
    
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'user', 'user_name', 'comment', 'is_internal', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
