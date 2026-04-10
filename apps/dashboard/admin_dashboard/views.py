from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta

from apps.dashboard.permissions import IsAdminUser
from .models import AdminCampaign, AdminTarget, SystemSettings, AuditLog
from apps.dashboard.saler_dashboard.models import Campaign, Contact, Lead, Target
from apps.dashboard.manager_dashboard.models import ManagerCampaign, ManagerTarget
from apps.calling.models import Call, CallStatus
from apps.account.models import User, UserType
from .serializers import (
    AdminCampaignSerializer, AdminTargetSerializer, SystemSettingsSerializer,
    AuditLogSerializer, CampaignListSerializer, ContactListSerializer,
    LeadListSerializer, TargetListSerializer, ManagerTargetListSerializer,
    AdminDashboardStatsSerializer, AdminAgentPerformanceSerializer,
    AdminCampaignStatsSerializer, AdminCallListSerializer,
    AdminUserSerializer, LeadAssignSerializer, BulkActionSerializer
)


def log_audit(request, action, model_name, object_id=None, changes=None):
    """Helper function to log admin actions"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    AuditLog.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        changes=changes or {},
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


class AdminCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing admin-level campaigns"""
    queryset = AdminCampaign.objects.all()
    serializer_class = AdminCampaignSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return AdminCampaign.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        log_audit(self.request, 'create', 'AdminCampaign', 
                  object_id=serializer.instance.id if serializer.instance else None,
                  changes={'action': 'created campaign'})
    
    def perform_update(self, serializer):
        old_data = AdminCampaignSerializer(self.instance).data
        serializer.save()
        new_data = AdminCampaignSerializer(self.instance).data
        changes = {k: {'old': old_data.get(k), 'new': new_data.get(k)} 
                   for k in old_data.keys() if old_data.get(k) != new_data.get(k)}
        log_audit(self.request, 'update', 'AdminCampaign', 
                  object_id=self.instance.id, changes=changes)
    
    def perform_destroy(self, instance):
        log_audit(self.request, 'delete', 'AdminCampaign', 
                  object_id=instance.id, changes={'name': instance.name})
        instance.delete()


class AdminTargetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing admin-level targets"""
    queryset = AdminTarget.objects.all()
    serializer_class = AdminTargetSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return AdminTarget.objects.all().order_by('-period_end')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        log_audit(self.request, 'create', 'AdminTarget',
                  object_id=serializer.instance.id if serializer.instance else None)
    
    def perform_update(self, serializer):
        old_data = AdminTargetSerializer(self.instance).data
        serializer.save()
        log_audit(self.request, 'update', 'AdminTarget',
                  object_id=self.instance.id)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing system settings"""
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return SystemSettings.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        log_audit(self.request, 'create', 'SystemSettings',
                  object_id=serializer.instance.id if serializer.instance else None,
                  changes={'key': serializer.instance.key})
    
    def perform_update(self, serializer):
        old_data = SystemSettingsSerializer(self.instance).data
        serializer.save()
        log_audit(self.request, 'update', 'SystemSettings',
                  object_id=self.instance.id)
    
    def perform_destroy(self, instance):
        log_audit(self.request, 'delete', 'SystemSettings',
                  object_id=instance.id, changes={'key': instance.key})
        instance.delete()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing audit logs"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        queryset = AuditLog.objects.all()
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by model
        model_name = self.request.query_params.get('model_name')
        if model_name:
            queryset = queryset.filter(model_name=model_name)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset.order_by('-created_at')


class AllCampaignViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing all campaigns"""
    queryset = Campaign.objects.all()
    serializer_class = CampaignListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return Campaign.objects.all().order_by('-created_at')


class AllContactViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing all contacts"""
    queryset = Contact.objects.all()
    serializer_class = ContactListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return Contact.objects.all().order_by('-created_at')


class AllLeadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing all leads at admin level"""
    queryset = Lead.objects.all()
    serializer_class = LeadListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return Lead.objects.all().order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def assign_lead(self, request):
        """Assign lead to an agent"""
        serializer = LeadAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        lead_id = serializer.validated_data['lead_id']
        assigned_to_id = serializer.validated_data['assigned_to_id']
        
        try:
            lead = Lead.objects.get(id=lead_id)
            agent = User.objects.get(id=assigned_to_id)
            old_assigned = lead.assigned_to
            lead.assigned_to = agent
            lead.save()
            log_audit(request, 'assign_lead', 'Lead',
                      object_id=lead.id,
                      changes={'old_assigned': str(old_assigned.id) if old_assigned else None,
                              'new_assigned': str(agent.id)})
            return Response(LeadListSerializer(lead).data)
        except Lead.DoesNotExist:
            return Response(
                {'error': 'Lead not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'Agent not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on leads"""
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        object_ids = serializer.validated_data['object_ids']
        
        leads = Lead.objects.filter(id__in=object_ids)
        
        if action == 'delete':
            count = leads.count()
            leads.delete()
            log_audit(request, 'bulk_delete', 'Lead',
                      changes={'count': count, 'ids': [str(id) for id in object_ids]})
            return Response({'message': f'{count} leads deleted'})
        
        elif action == 'update_status':
            new_status = serializer.validated_data.get('data', {}).get('status')
            if not new_status:
                return Response({'error': 'status required'}, status=status.HTTP_400_BAD_REQUEST)
            old_status = leads.first().status if leads.exists() else None
            leads.update(status=new_status)
            log_audit(request, 'bulk_update_status', 'Lead',
                      changes={'old_status': old_status, 'new_status': new_status,
                              'count': leads.count()})
            return Response({'message': f'{leads.count()} leads updated'})
        
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """Get all unassigned leads"""
        leads = Lead.objects.filter(assigned_to__isnull=True).order_by('-created_at')
        serializer = LeadListSerializer(leads, many=True)
        return Response(serializer.data)


class AllTargetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing all targets"""
    queryset = Target.objects.all()
    serializer_class = TargetListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        return Target.objects.all().order_by('-period_end')


class AdminDashboardViewSet(viewsets.ViewSet):
    """ViewSet for admin dashboard statistics"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def stats(self, request):
        """Get overall dashboard statistics"""
        today = timezone.now().date()
        
        # Get all calls
        calls = Call.objects.all()
        
        # Total calls
        total_calls = calls.count()
        
        # Successful calls
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        
        # Missed/failed calls
        missed_calls = calls.filter(status=CallStatus.FAILED).count()
        
        # User counts by type
        total_agents = User.objects.filter(user_type__in=[UserType.SELLS, UserType.MARKETING]).count()
        total_managers = User.objects.filter(user_type=UserType.MANAGER).count()
        total_admins = User.objects.filter(user_type__in=[UserType.ADMIN, UserType.SUPER_ADMIN]).count()
        
        # Active campaigns
        active_campaigns = Campaign.objects.filter(status='active').count()
        total_campaigns = Campaign.objects.count()
        
        # Total leads
        total_leads = Lead.objects.count()
        converted_leads = Lead.objects.filter(status='converted').count()
        
        # Total contacts
        total_contacts = Contact.objects.count()
        
        # Total duration
        total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        
        # Average duration
        avg_duration = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
        # Success rate
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Lead conversion rate
        lead_conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        data = {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'missed_calls': missed_calls,
            'total_agents': total_agents,
            'total_managers': total_managers,
            'total_admins': total_admins,
            'active_campaigns': active_campaigns,
            'total_campaigns': total_campaigns,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'total_contacts': total_contacts,
            'total_call_duration': total_duration,
            'average_call_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2),
            'lead_conversion_rate': round(lead_conversion_rate, 2)
        }
        
        serializer = AdminDashboardStatsSerializer(data)
        return Response(serializer.data)
    
    def recent_calls(self, request):
        """Get recent calls"""
        limit = request.query_params.get('limit', 20)
        try:
            limit = int(limit)
        except ValueError:
            limit = 20
        
        calls = Call.objects.all().order_by('-created_at')[:limit]
        serializer = AdminCallListSerializer(calls, many=True)
        return Response(serializer.data)
    
    def campaigns(self, request):
        """Get all campaigns"""
        campaigns = Campaign.objects.all().order_by('-created_at')
        serializer = CampaignListSerializer(campaigns, many=True)
        return Response(serializer.data)
    
    def contacts(self, request):
        """Get all contacts"""
        contacts = Contact.objects.all().order_by('-created_at')
        serializer = ContactListSerializer(contacts, many=True)
        return Response(serializer.data)
    
    def leads(self, request):
        """Get all leads"""
        leads = Lead.objects.all().order_by('-created_at')
        serializer = LeadListSerializer(leads, many=True)
        return Response(serializer.data)
    
    def targets(self, request):
        """Get all targets"""
        targets = Target.objects.all().order_by('-period_end')
        serializer = TargetListSerializer(targets, many=True)
        return Response(serializer.data)
    
    def performance(self, request):
        """Get performance data across all agents"""
        today = timezone.now().date()
        
        # Daily stats
        daily_calls = Call.objects.filter(created_at__date=today).count()
        daily_successful = Call.objects.filter(
            created_at__date=today,
            status=CallStatus.COMPLETED
        ).count()
        
        # Weekly stats
        week_start = today - timedelta(days=today.weekday())
        weekly_calls = Call.objects.filter(created_at__date__gte=week_start).count()
        weekly_successful = Call.objects.filter(
            created_at__date__gte=week_start,
            status=CallStatus.COMPLETED
        ).count()
        
        # Monthly stats
        month_start = today.replace(day=1)
        monthly_calls = Call.objects.filter(created_at__date__gte=month_start).count()
        monthly_successful = Call.objects.filter(
            created_at__date__gte=month_start,
            status=CallStatus.COMPLETED
        ).count()
        
        data = {
            'daily': {
                'total_calls': daily_calls,
                'successful_calls': daily_successful,
                'success_rate': round((daily_successful / daily_calls * 100) if daily_calls > 0 else 0, 2)
            },
            'weekly': {
                'total_calls': weekly_calls,
                'successful_calls': weekly_successful,
                'success_rate': round((weekly_successful / weekly_calls * 100) if weekly_calls > 0 else 0, 2)
            },
            'monthly': {
                'total_calls': monthly_calls,
                'successful_calls': monthly_successful,
                'success_rate': round((monthly_successful / monthly_calls * 100) if monthly_calls > 0 else 0, 2)
            }
        }
        
        return Response(data)
    
    def call_status_distribution(self, request):
        """Get call status distribution"""
        status_counts = Call.objects.values('status').annotate(count=Count('id'))
        
        data = {}
        for item in status_counts:
            data[item['status']] = item['count']
        
        return Response(data)
    
    def top_performing_agents(self, request):
        """Get top performing agents"""
        agents = User.objects.filter(
            user_type__in=[UserType.SELLS, UserType.MARKETING, UserType.MANAGER]
        ).filter(is_active=True)
        
        agent_performance = []
        for agent in agents:
            total_calls = Call.objects.filter(user=agent).count()
            successful_calls = Call.objects.filter(
                user=agent, 
                status=CallStatus.COMPLETED
            ).count()
            missed_calls = Call.objects.filter(
                user=agent,
                status=CallStatus.FAILED
            ).count()
            
            total_duration = Call.objects.filter(user=agent).aggregate(
                Sum('duration_seconds')
            )['duration_seconds__sum'] or 0
            
            avg_duration = Call.objects.filter(
                user=agent,
                status=CallStatus.COMPLETED
            ).aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
            
            leads_assigned = Lead.objects.filter(assigned_to=agent).count()
            leads_converted = Lead.objects.filter(
                assigned_to=agent,
                status='converted'
            ).count()
            
            # Revenue from converted leads
            revenue = Lead.objects.filter(
                assigned_to=agent,
                status='converted'
            ).aggregate(Sum('value'))['value__sum'] or 0
            
            agent_performance.append({
                'agent_id': agent.id,
                'agent_name': agent.name or agent.email,
                'agent_email': agent.email,
                'user_type': agent.user_type,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'missed_calls': missed_calls,
                'total_duration': total_duration,
                'average_duration': round(avg_duration, 2),
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'leads_assigned': leads_assigned,
                'leads_converted': leads_converted,
                'revenue_generated': float(revenue)
            })
        
        # Sort by successful calls
        agent_performance.sort(key=lambda x: x['successful_calls'], reverse=True)
        
        return Response(agent_performance[:10])
    
    def campaign_stats(self, request):
        """Get statistics for all campaigns"""
        campaigns = Campaign.objects.all()
        
        campaign_stats = []
        for campaign in campaigns:
            leads = Lead.objects.filter(campaign=campaign)
            total_leads = leads.count()
            converted_leads = leads.filter(status='converted').count()
            
            # Get calls related to this campaign
            campaign_contacts = Contact.objects.filter(campaign=campaign)
            customer_numbers = campaign_contacts.values_list('phone_number', flat=True)
            total_calls = Call.objects.filter(customer_number__in=customer_numbers).count()
            successful_calls = Call.objects.filter(
                customer_number__in=customer_numbers,
                status=CallStatus.COMPLETED
            ).count()
            
            campaign_stats.append({
                'campaign_id': campaign.id,
                'campaign_name': campaign.name,
                'status': campaign.status,
                'total_leads': total_leads,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'converted_leads': converted_leads,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'conversion_rate': round((converted_leads / total_leads * 100) if total_leads > 0 else 0, 2)
            })
        
        serializer = AdminCampaignStatsSerializer(campaign_stats, many=True)
        return Response(serializer.data)
    
    def users(self, request):
        """Get all users with their stats"""
        user_type = request.query_params.get('user_type')
        
        if user_type:
            users = User.objects.filter(user_type=user_type, is_active=True)
        else:
            users = User.objects.filter(is_active=True)
        
        data = []
        for user in users:
            total_calls = Call.objects.filter(user=user).count()
            successful_calls = Call.objects.filter(
                user=user,
                status=CallStatus.COMPLETED
            ).count()
            
            data.append({
                'id': user.id,
                'name': user.name or user.email,
                'email': user.email,
                'phone_number': user.phone_number,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'created_at': user.created_at
            })
        
        return Response(data)
    
    def lead_status_distribution(self, request):
        """Get lead status distribution"""
        status_counts = Lead.objects.values('status').annotate(count=Count('id'))
        
        data = {}
        for item in status_counts:
            data[item['status']] = item['count']
        
        return Response(data)
    
    def daily_performance(self, request):
        """Get daily performance for the last 30 days"""
        today = timezone.now().date()
        days = int(request.query_params.get('days', 30))
        
        daily_data = []
        for i in range(days):
            date = today - timedelta(days=i)
            daily_calls = Call.objects.filter(created_at__date=date).count()
            successful_calls = Call.objects.filter(
                created_at__date=date,
                status=CallStatus.COMPLETED
            ).count()
            
            daily_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'total_calls': daily_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / daily_calls * 100) if daily_calls > 0 else 0, 2)
            })
        
        return Response(list(reversed(daily_data)))


class UserManagementViewSet(viewsets.ViewSet):
    """ViewSet for user management operations"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list_users(self, request):
        """Get all users with filtering options"""
        user_type = request.query_params.get('user_type')
        is_active = request.query_params.get('is_active')
        
        users = User.objects.all()
        
        if user_type:
            users = users.filter(user_type=user_type)
        
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        
        data = []
        for user in users:
            total_calls = Call.objects.filter(user=user).count()
            successful_calls = Call.objects.filter(
                user=user,
                status=CallStatus.COMPLETED
            ).count()
            
            data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number,
                'user_type': user.user_type,
                'is_active': user.is_active,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'created_at': user.created_at
            })
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle user active status"""
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            log_audit(request, 'toggle_active', 'User',
                      object_id=user.id,
                      changes={'is_active': user.is_active})
            return Response({
                'id': user.id,
                'is_active': user.is_active,
                'message': f"User {'activated' if user.is_active else 'deactivated'}"
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def change_user_type(self, request, pk=None):
        """Change user type"""
        new_type = request.data.get('user_type')
        
        if not new_type:
            return Response(
                {'error': 'user_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_type not in UserType.values:
            return Response(
                {'error': 'Invalid user type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(pk=pk)
            old_type = user.user_type
            user.user_type = new_type
            user.save()
            log_audit(request, 'change_user_type', 'User',
                      object_id=user.id,
                      changes={'old_type': old_type, 'new_type': new_type})
            return Response({
                'id': user.id,
                'user_type': user.user_type,
                'message': 'User type updated'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def agents(self, request):
        """Get all agents (sells and marketing users)"""
        agents = User.objects.filter(
            user_type__in=[UserType.SELLS, UserType.MARKETING],
            is_active=True
        )
        
        data = []
        for agent in agents:
            total_calls = Call.objects.filter(user=agent).count()
            successful_calls = Call.objects.filter(
                user=agent,
                status=CallStatus.COMPLETED
            ).count()
            
            data.append({
                'id': agent.id,
                'name': agent.name or agent.email,
                'email': agent.email,
                'phone_number': agent.phone_number,
                'user_type': agent.user_type,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2)
            })
        
        return Response(data)
    
    def managers(self, request):
        """Get all managers"""
        managers = User.objects.filter(
            user_type=UserType.MANAGER,
            is_active=True
        )
        
        data = []
        for manager in managers:
            total_calls = Call.objects.filter(user=manager).count()
            
            data.append({
                'id': manager.id,
                'name': manager.name or manager.email,
                'email': manager.email,
                'phone_number': manager.phone_number,
                'user_type': manager.user_type,
                'total_calls': total_calls
            })
        
        return Response(data)
