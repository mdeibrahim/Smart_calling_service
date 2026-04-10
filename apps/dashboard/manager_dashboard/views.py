from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta

from apps.dashboard.permissions import IsManagerUser
from .models import ManagerCampaign, ManagerTarget
from apps.dashboard.saler_dashboard.models import Campaign, Contact, Lead, Target
from apps.calling.models import Call, CallStatus
from apps.account.models import User, UserType
from .serializers import (
    ManagerCampaignSerializer, ContactSerializer, LeadSerializer,
    ManagerTargetSerializer, TargetSerializer,
    DashboardStatsSerializer, AgentPerformanceSerializer,
    CampaignStatsSerializer, CallListSerializer, LeadAssignSerializer
)


class ManagerCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing campaigns at manager level - shows all campaigns"""
    queryset = ManagerCampaign.objects.all()
    serializer_class = ManagerCampaignSerializer
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def get_queryset(self):
        # Managers see all campaigns
        return ManagerCampaign.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AllCampaignViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing all campaigns from saler_dashboard"""
    queryset = Campaign.objects.all()
    serializer_class = ManagerCampaignSerializer
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def get_queryset(self):
        return Campaign.objects.all().order_by('-created_at')


class AllContactViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing all contacts at manager level"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def get_queryset(self):
        return Contact.objects.all().order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def assign_campaign(self, request, pk=None):
        """Assign contact to a campaign"""
        contact = self.get_object()
        campaign_id = request.data.get('campaign_id')
        
        if not campaign_id:
            return Response(
                {'error': 'campaign_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            campaign = Campaign.objects.get(id=campaign_id)
            contact.campaign = campaign
            contact.save()
            return Response(ContactSerializer(contact).data)
        except Campaign.DoesNotExist:
            return Response(
                {'error': 'Campaign not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AllLeadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing all leads at manager level"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def get_queryset(self):
        # Managers see all leads
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
            lead.assigned_to = agent
            lead.save()
            return Response(LeadSerializer(lead).data)
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
    
    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """Get all unassigned leads"""
        leads = Lead.objects.filter(assigned_to__isnull=True).order_by('-created_at')
        serializer = LeadSerializer(leads, many=True)
        return Response(serializer.data)


class ManagerTargetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing targets at manager level"""
    queryset = ManagerTarget.objects.all()
    serializer_class = ManagerTargetSerializer
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def get_queryset(self):
        return ManagerTarget.objects.all().order_by('-period_end')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AllTargetViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing all targets"""
    queryset = Target.objects.all()
    serializer_class = TargetSerializer
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def get_queryset(self):
        return Target.objects.all().order_by('-period_end')


class ManagerDashboardViewSet(viewsets.ViewSet):
    """ViewSet for manager dashboard statistics - shows data across all agents"""
    permission_classes = [IsAuthenticated, IsManagerUser]
    
    def stats(self, request):
        """Get overall dashboard statistics for all agents"""
        today = timezone.now().date()
        
        # Get all calls
        calls = Call.objects.all()
        
        # Total calls
        total_calls = calls.count()
        
        # Successful calls
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        
        # Missed/failed calls
        missed_calls = calls.filter(status=CallStatus.FAILED).count()
        
        # Total agents
        total_agents = User.objects.filter(user_type__in=[UserType.SELLS, UserType.MARKETING, UserType.MANAGER]).count()
        
        # Active campaigns
        active_campaigns = Campaign.objects.filter(status='active').count()
        
        # Total leads
        total_leads = Lead.objects.count()
        
        # Converted leads
        converted_leads = Lead.objects.filter(status='converted').count()
        
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
            'active_campaigns': active_campaigns,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'total_call_duration': total_duration,
            'average_call_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2),
            'lead_conversion_rate': round(lead_conversion_rate, 2)
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
    
    def recent_calls(self, request):
        """Get recent calls from all agents"""
        limit = request.query_params.get('limit', 20)
        try:
            limit = int(limit)
        except ValueError:
            limit = 20
        
        calls = Call.objects.all().order_by('-created_at')[:limit]
        serializer = CallListSerializer(calls, many=True)
        return Response(serializer.data)
    
    def campaigns(self, request):
        """Get all campaigns"""
        campaigns = Campaign.objects.all().order_by('-created_at')
        serializer = ManagerCampaignSerializer(campaigns, many=True)
        return Response(serializer.data)
    
    def contacts(self, request):
        """Get all contacts"""
        contacts = Contact.objects.all().order_by('-created_at')
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    def leads(self, request):
        """Get all leads"""
        leads = Lead.objects.all().order_by('-created_at')
        serializer = LeadSerializer(leads, many=True)
        return Response(serializer.data)
    
    def targets(self, request):
        """Get all targets"""
        targets = Target.objects.all().order_by('-period_end')
        serializer = TargetSerializer(targets, many=True)
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
        """Get call status distribution across all agents"""
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
                'leads_converted': leads_converted
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
        
        serializer = CampaignStatsSerializer(campaign_stats, many=True)
        return Response(serializer.data)
    
    def agents(self, request):
        """Get all agents"""
        user_type = request.query_params.get('user_type')
        
        if user_type:
            agents = User.objects.filter(user_type=user_type, is_active=True)
        else:
            agents = User.objects.filter(
                user_type__in=[UserType.SELLS, UserType.MARKETING, UserType.MANAGER],
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
                'is_active': agent.is_active,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'created_at': agent.created_at
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
