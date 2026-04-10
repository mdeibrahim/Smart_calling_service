from django.db import models
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.account.models import UserType
from apps.dashboard.permissions import IsAdminOrManagerOrAuditor, IsSupportUser
from apps.dashboard.support_dashboard.models import SupportTicket, TicketComment
from apps.dashboard.support_dashboard.serializers import (
    SupportTicketSerializer,
    SupportTicketCreateSerializer,
    SupportTicketUpdateSerializer,
    TicketCommentSerializer,
)
from apps.calling.models import Call


class SupportTicketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing support tickets"""
    
    queryset = SupportTicket.objects.all()
    permission_classes = [IsAuthenticated, IsSupportUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'assigned_to']
    search_fields = ['ticket_number', 'subject', 'customer_name', 'customer_phone']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SupportTicketUpdateSerializer
        return SupportTicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Managers can see all tickets
        if user.user_type in [UserType.SUPER_ADMIN, UserType.ADMIN, UserType.MANAGER]:
            return SupportTicket.objects.all()
        
        # Support users see tickets they created or are assigned to
        return SupportTicket.objects.filter(
            models.Q(assigned_to=user) | models.Q(created_by=user)
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment to a ticket"""
        ticket = self.get_object()
        serializer = TicketCommentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(ticket=ticket, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to a user"""
        ticket = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.account.models import User
        try:
            user = User.objects.get(id=user_id)
            ticket.assigned_to = user
            ticket.save()
            return Response(SupportTicketSerializer(ticket).data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark ticket as resolved"""
        ticket = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        ticket.status = 'resolved'
        ticket.resolution_notes = resolution_notes
        ticket.resolved_at = timezone.now()
        ticket.save()
        
        return Response(SupportTicketSerializer(ticket).data)


class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing call logs (read-only)"""
    
    from apps.calling.serializers import CallSerializer
    
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated, IsSupportUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'user']
    search_fields = ['customer_number', 'seller_number', 'twilio_call_sid']
    ordering_fields = ['created_at', 'started_at', 'ended_at', 'duration_seconds']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Admins and Managers can see all calls
        if user.user_type in [UserType.SUPER_ADMIN, UserType.ADMIN, UserType.MANAGER]:
            return Call.objects.all()
        
        # Others see only their own calls
        return Call.objects.filter(user=user)
