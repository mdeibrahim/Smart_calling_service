from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta

from apps.dashboard.permissions import IsAuditorUser
from .models import AuditorSettings, AuditorFilterPreset, AuditorBookmark
from apps.dashboard.saler_dashboard.models import Campaign, Contact, Lead
from apps.calling.models import Call, CallStatus
from apps.account.models import User, UserType

from .serializers import (
    AuditorSettingsSerializer, AuditorFilterPresetSerializer,
    AuditorBookmarkSerializer, AuditorCallListSerializer,
    AuditorCallDetailSerializer, AuditorCampaignListSerializer,
    AuditorContactListSerializer, AuditorLeadListSerializer,
    AuditorDashboardStatsSerializer, AuditorAgentPerformanceSerializer,
    AuditorCampaignPerformanceSerializer, CallTranscriptSerializer,
    CallReportSerializer
)


class AuditorSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing auditor settings"""
    queryset = AuditorSettings.objects.all()
    serializer_class = AuditorSettingsSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        return AuditorSettings.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """Get current user's settings"""
        settings, created = AuditorSettings.objects.get_or_create(user=request.user)
        serializer = AuditorSettingsSerializer(settings)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_settings(self, request):
        """Update current user's settings"""
        settings, created = AuditorSettings.objects.get_or_create(user=request.user)
        serializer = AuditorSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AuditorFilterPresetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing auditor filter presets"""
    queryset = AuditorFilterPreset.objects.all()
    serializer_class = AuditorFilterPresetSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        return AuditorFilterPreset.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')
    
    def perform_create(self, serializer):
        # If this preset is default, unset other defaults
        if serializer.validated_data.get('is_default', False):
            AuditorFilterPreset.objects.filter(
                user=self.request.user,
                is_default=True
            ).update(is_default=False)
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        if serializer.validated_data.get('is_default', False):
            AuditorFilterPreset.objects.filter(
                user=self.request.user,
                is_default=True
            ).exclude(id=self.instance.id).update(is_default=False)
        serializer.save()


class AuditorBookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for managing auditor bookmarks"""
    queryset = AuditorBookmark.objects.all()
    serializer_class = AuditorBookmarkSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        return AuditorBookmark.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AuditorCallHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing call history in auditor dashboard"""
    queryset = Call.objects.all()
    serializer_class = AuditorCallListSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        queryset = Call.objects.all().order_by('-created_at')
        
        # Filter by user (agent)
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by status
        call_status = self.request.query_params.get('status')
        if call_status:
            queryset = queryset.filter(status=call_status)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Filter by phone number
        phone = self.request.query_params.get('phone')
        if phone:
            queryset = queryset.filter(
                Q(customer_number__icontains=phone) | 
                Q(seller_number__icontains=phone)
            )
        
        # Filter by duration (greater than)
        min_duration = self.request.query_params.get('min_duration')
        if min_duration:
            queryset = queryset.filter(duration_seconds__gte=int(min_duration))
        
        # Filter by duration (less than)
        max_duration = self.request.query_params.get('max_duration')
        if max_duration:
            queryset = queryset.filter(duration_seconds__lte=int(max_duration))
        
        # Filter calls with transcripts
        has_transcript = self.request.query_params.get('has_transcript')
        if has_transcript == 'true':
            from apps.calling.models import CallTranscript
            call_ids_with_transcript = CallTranscript.objects.values_list('call_id', flat=True).distinct()
            queryset = queryset.filter(id__in=call_ids_with_transcript)
        
        # Filter calls with reports
        has_report = self.request.query_params.get('has_report')
        if has_report == 'true':
            from apps.calling.models import CallReport
            call_ids_with_report = CallReport.objects.values_list('call_id', flat=True).distinct()
            queryset = queryset.filter(id__in=call_ids_with_report)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(customer_number__icontains=search) |
                Q(seller_number__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Pagination
        page_size = self.request.query_params.get('page_size', 20)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 20
        
        return queryset[:page_size * 2]  # Return more for pagination
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get detailed call information with transcripts and reports"""
        try:
            call = Call.objects.get(pk=pk)
        except Call.DoesNotExist:
            return Response(
                {'error': 'Call not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has settings to determine what to show
        try:
            settings = AuditorSettings.objects.get(user=request.user)
            serializer = AuditorCallDetailSerializer(call)
            data = serializer.data
            
            # Hide transcripts if settings say so
            if not settings.show_transcripts:
                data['transcripts'] = []
            
            # Hide report if settings say so
            if not settings.show_reports:
                data['report'] = None
            
            return Response(data)
        except AuditorSettings.DoesNotExist:
            serializer = AuditorCallDetailSerializer(call)
            return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export calls as CSV data"""
        queryset = self.get_queryset()
        # Return data in exportable format
        data = []
        for call in queryset:
            data.append({
                'id': call.id,
                'user': call.user.name or call.user.email,
                'seller_number': call.seller_number,
                'customer_number': call.customer_number,
                'status': call.status,
                'duration_seconds': call.duration_seconds,
                'started_at': call.started_at,
                'ended_at': call.ended_at,
                'created_at': call.created_at
            })
        return Response(data)


class AuditorCallReportsViewSet(viewsets.ViewSet):
    """ViewSet for call reports and analytics in auditor dashboard"""
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def stats(self, request):
        """Get overall call statistics"""
        today = timezone.now().date()
        
        calls = Call.objects.all()
        
        total_calls = calls.count()
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        failed_calls = calls.filter(status=CallStatus.FAILED).count()
        
        total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        avg_duration = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        total_campaigns = Campaign.objects.count()
        active_campaigns = Campaign.objects.filter(status='active').count()
        
        total_contacts = Contact.objects.count()
        total_leads = Lead.objects.count()
        converted_leads = Lead.objects.filter(status='converted').count()
        
        lead_conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        data = {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_duration': total_duration,
            'average_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2),
            'total_campaigns': total_campaigns,
            'active_campaigns': active_campaigns,
            'total_contacts': total_contacts,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'lead_conversion_rate': round(lead_conversion_rate, 2)
        }
        
        serializer = AuditorDashboardStatsSerializer(data)
        return Response(serializer.data)
    
    def daily_stats(self, request):
        """Get daily call statistics"""
        today = timezone.now().date()
        
        calls = Call.objects.filter(created_at__date=today)
        
        total_calls = calls.count()
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        failed_calls = calls.filter(status=CallStatus.FAILED).count()
        total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        avg_duration = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        return Response({
            'date': today,
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_duration': total_duration,
            'average_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2)
        })
    
    def weekly_stats(self, request):
        """Get weekly call statistics"""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        calls = Call.objects.filter(created_at__date__gte=week_start)
        
        total_calls = calls.count()
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        failed_calls = calls.filter(status=CallStatus.FAILED).count()
        total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        avg_duration = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        return Response({
            'week_start': week_start,
            'week_end': today,
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_duration': total_duration,
            'average_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2)
        })
    
    def monthly_stats(self, request):
        """Get monthly call statistics"""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        calls = Call.objects.filter(created_at__date__gte=month_start)
        
        total_calls = calls.count()
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        failed_calls = calls.filter(status=CallStatus.FAILED).count()
        total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        avg_duration = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        return Response({
            'month_start': month_start,
            'month_end': today,
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'total_duration': total_duration,
            'average_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2)
        })
    
    def call_status_distribution(self, request):
        """Get call status distribution"""
        status_counts = Call.objects.values('status').annotate(count=Count('id'))
        
        data = {}
        for item in status_counts:
            data[item['status']] = item['count']
        
        return Response(data)
    
    def agent_performance(self, request):
        """Get performance data for all agents"""
        # Get date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        agents = User.objects.filter(
            user_type__in=[UserType.SELLS, UserType.MARKETING, UserType.MANAGER]
        ).filter(is_active=True)
        
        agent_performance = []
        for agent in agents:
            calls = Call.objects.filter(user=agent)
            
            if start_date:
                calls = calls.filter(created_at__date__gte=start_date)
            if end_date:
                calls = calls.filter(created_at__date__lte=end_date)
            
            total_calls = calls.count()
            successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
            failed_calls = calls.filter(status=CallStatus.FAILED).count()
            
            total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
            avg_duration = calls.filter(status=CallStatus.COMPLETED).aggregate(
                Avg('duration_seconds')
            )['duration_seconds__avg'] or 0
            
            leads_assigned = Lead.objects.filter(assigned_to=agent).count()
            converted_leads = Lead.objects.filter(
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
                'failed_calls': failed_calls,
                'total_duration': total_duration,
                'average_duration': round(avg_duration, 2),
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'leads_assigned': leads_assigned,
                'converted_leads': converted_leads
            })
        
        # Sort by successful calls
        agent_performance.sort(key=lambda x: x['successful_calls'], reverse=True)
        
        return Response(agent_performance[:50])
    
    def campaign_performance(self, request):
        """Get performance data for all campaigns"""
        campaigns = Campaign.objects.all()
        
        campaign_performance = []
        for campaign in campaigns:
            contacts = Contact.objects.filter(campaign=campaign)
            customer_numbers = contacts.values_list('phone_number', flat=True)
            
            leads = Lead.objects.filter(campaign=campaign)
            total_leads = leads.count()
            converted_leads = leads.filter(status='converted').count()
            
            calls = Call.objects.filter(customer_number__in=customer_numbers)
            total_calls = calls.count()
            successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
            failed_calls = calls.filter(status=CallStatus.FAILED).count()
            
            campaign_performance.append({
                'campaign_id': campaign.id,
                'campaign_name': campaign.name,
                'status': campaign.status,
                'total_contacts': contacts.count(),
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'total_leads': total_leads,
                'converted_leads': converted_leads,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'conversion_rate': round((converted_leads / total_leads * 100) if total_leads > 0 else 0, 2)
            })
        
        # Sort by successful calls
        campaign_performance.sort(key=lambda x: x['successful_calls'], reverse=True)
        
        return Response(campaign_performance[:50])
    
    def duration_distribution(self, request):
        """Get call duration distribution"""
        durations = Call.objects.filter(
            duration_seconds__isnull=False
        ).values('duration_seconds')
        
        buckets = {
            '0-30s': 0,
            '31-60s': 0,
            '1-3min': 0,
            '3-5min': 0,
            '5-10min': 0,
            '10min+': 0
        }
        
        for call in durations:
            ds = call['duration_seconds']
            if ds <= 30:
                buckets['0-30s'] += 1
            elif ds <= 60:
                buckets['31-60s'] += 1
            elif ds <= 180:
                buckets['1-3min'] += 1
            elif ds <= 300:
                buckets['3-5min'] += 1
            elif ds <= 600:
                buckets['5-10min'] += 1
            else:
                buckets['10min+'] += 1
        
        return Response(buckets)


class AuditorCampaignsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing campaigns in auditor dashboard"""
    queryset = Campaign.objects.all()
    serializer_class = AuditorCampaignListSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        queryset = Campaign.objects.all().order_by('-created_at')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset


class AuditorContactsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing contacts in auditor dashboard"""
    queryset = Contact.objects.all()
    serializer_class = AuditorContactListSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        queryset = Contact.objects.all().order_by('-created_at')
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(company__icontains=search)
            )
        
        return queryset


class AuditorLeadsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing leads in auditor dashboard"""
    queryset = Lead.objects.all()
    serializer_class = AuditorLeadListSerializer
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def get_queryset(self):
        queryset = Lead.objects.all().order_by('-created_at')
        
        # Filter by campaign
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)
        
        # Filter by status
        lead_status = self.request.query_params.get('status')
        if lead_status:
            queryset = queryset.filter(status=lead_status)
        
        # Filter by assigned agent
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(assigned_to_id=agent_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(contact__name__icontains=search) |
                Q(contact__phone_number__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset


class AuditorDashboardViewSet(viewsets.ViewSet):
    """ViewSet for auditor dashboard"""
    permission_classes = [IsAuthenticated, IsAuditorUser]
    
    def overview(self, request):
        """Get dashboard overview"""
        today = timezone.now().date()
        
        # Today's stats
        today_calls = Call.objects.filter(created_at__date=today)
        today_total = today_calls.count()
        today_successful = today_calls.filter(status=CallStatus.COMPLETED).count()
        
        # This week's stats
        week_start = today - timedelta(days=today.weekday())
        week_calls = Call.objects.filter(created_at__date__gte=week_start)
        week_total = week_calls.count()
        week_successful = week_calls.filter(status=CallStatus.COMPLETED).count()
        
        # This month's stats
        month_start = today.replace(day=1)
        month_calls = Call.objects.filter(created_at__date__gte=month_start)
        month_total = month_calls.count()
        month_successful = month_calls.filter(status=CallStatus.COMPLETED).count()
        
        # All time
        total_calls = Call.objects.count()
        total_successful = Call.objects.filter(status=CallStatus.COMPLETED).count()
        
        # Campaigns
        active_campaigns = Campaign.objects.filter(status='active').count()
        
        # Leads
        total_leads = Lead.objects.count()
        converted_leads = Lead.objects.filter(status='converted').count()
        
        return Response({
            'today': {
                'total_calls': today_total,
                'successful_calls': today_successful,
                'success_rate': round((today_successful / today_total * 100) if today_total > 0 else 0, 2)
            },
            'this_week': {
                'total_calls': week_total,
                'successful_calls': week_successful,
                'success_rate': round((week_successful / week_total * 100) if week_total > 0 else 0, 2)
            },
            'this_month': {
                'total_calls': month_total,
                'successful_calls': month_successful,
                'success_rate': round((month_successful / month_total * 100) if month_total > 0 else 0, 2)
            },
            'all_time': {
                'total_calls': total_calls,
                'successful_calls': total_successful,
                'success_rate': round((total_successful / total_calls * 100) if total_calls > 0 else 0, 2)
            },
            'active_campaigns': active_campaigns,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'lead_conversion_rate': round((converted_leads / total_leads * 100) if total_leads > 0 else 0, 2)
        })
    
    def recent_calls(self, request):
        """Get recent calls"""
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        calls = Call.objects.all().order_by('-created_at')[:limit]
        serializer = AuditorCallListSerializer(calls, many=True)
        return Response(serializer.data)
    
    def top_agents(self, request):
        """Get top performing agents"""
        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        agents = User.objects.filter(
            user_type__in=[UserType.SELLS, UserType.MARKETING]
        ).filter(is_active=True)
        
        agent_performance = []
        for agent in agents:
            calls = Call.objects.filter(user=agent)
            total_calls = calls.count()
            successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
            
            agent_performance.append({
                'agent_id': agent.id,
                'agent_name': agent.name or agent.email,
                'agent_email': agent.email,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2)
            })
        
        agent_performance.sort(key=lambda x: x['successful_calls'], reverse=True)
        return Response(agent_performance[:limit])
