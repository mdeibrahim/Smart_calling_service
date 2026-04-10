from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg, Q, Max
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import calendar

from .models import Campaign, Contact, Lead, LeadStatus, Target, CalibrationAudio, CalibrationSession, CalibrationAttempt
from apps.calling.models import Call, CallStatus, CallTranscript, TranscriptRole
from .serializers import (
    CampaignSerializer, ContactSerializer, LeadSerializer,
    TargetSerializer, DashboardStatsSerializer, CallListSerializer,
    CalibrationAudioSerializer, CalibrationAudioDetailSerializer,
    CalibrationAttemptSerializer, CalibrationAttemptUploadSerializer,
    CalibrationSessionSerializer,
)
from apps.dashboard.permissions import IsSalesUser
from apps.account.models import UserType


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing campaigns"""
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, IsSalesUser]
    
    def get_queryset(self):
        return Campaign.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing contacts"""
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated, IsSalesUser]
    
    def get_queryset(self):
        return Contact.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class LeadViewSet(viewsets.ModelViewSet):
    """ViewSet for managing leads"""
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsSalesUser]
    
    def get_queryset(self):
        return Lead.objects.filter(
            Q(assigned_to=self.request.user)
            | Q(contact__created_by=self.request.user)
            | Q(campaign__created_by=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        serializer.save(assigned_to=self.request.user)


class TargetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing targets"""
    queryset = Target.objects.all()
    serializer_class = TargetSerializer
    permission_classes = [IsAuthenticated, IsSalesUser]
    
    def get_queryset(self):
        return Target.objects.filter(user=self.request.user)


class DashboardViewSet(viewsets.ViewSet):
    """ViewSet for dashboard statistics and data"""
    permission_classes = [IsAuthenticated, IsSalesUser]
    
    def get_permissions(self):
        if self.action == 'stats':
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def stats(self, request):
        """Get dashboard statistics"""
        user = request.user
        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        # Get all calls for the user
        calls = Call.objects.filter(user=user)
        
        # Total calls
        total_calls = calls.count()
        
        # Successful calls (completed)
        successful_calls = calls.filter(status=CallStatus.COMPLETED).count()
        
        # Missed calls (failed)
        missed_calls = calls.filter(status=CallStatus.FAILED).count()
        
        # Total duration
        total_duration = calls.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        
        # Average duration
        avg_duration = calls.aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
        # Success rate
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Unique leads (contacts with at least one call)
        unique_leads = calls.values('customer_number').distinct().count()
        
        data = {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'missed_calls': missed_calls,
            'unique_leads': unique_leads,
            'total_call_duration': total_duration,
            'average_call_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2)
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
    
    def recent_calls(self, request):
        """Get recent calls"""
        calls = Call.objects.filter(user=request.user).order_by('-created_at')[:20]
        serializer = CallListSerializer(calls, many=True)
        return Response(serializer.data)
    
    def campaigns(self, request):
        """Get all campaigns"""
        campaigns = Campaign.objects.all().order_by('-created_at')
        serializer = CampaignSerializer(campaigns, many=True)
        return Response(serializer.data)
    
    def contacts(self, request):
        """Get all contacts"""
        contacts = Contact.objects.filter(created_by=request.user).order_by('-created_at')
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    def leads(self, request):
        """Get all leads"""
        leads = Lead.objects.filter(
            Q(assigned_to=request.user)
            | Q(contact__created_by=request.user)
            | Q(campaign__created_by=request.user)
        ).distinct().order_by('-created_at')
        serializer = LeadSerializer(leads, many=True)
        return Response(serializer.data)
    
    def targets(self, request):
        """Get user targets"""
        targets = Target.objects.filter(user=request.user).order_by('-period_end')
        serializer = TargetSerializer(targets, many=True)
        return Response(serializer.data)
    
    def performance(self, request):
        """Get agent performance data"""
        user = request.user
        today = timezone.now().date()
        
        # Daily stats
        daily_calls = Call.objects.filter(
            user=user, 
            created_at__date=today
        ).count()
        
        daily_successful = Call.objects.filter(
            user=user, 
            created_at__date=today,
            status=CallStatus.COMPLETED
        ).count()
        
        # Weekly stats
        week_start = today - timedelta(days=today.weekday())
        weekly_calls = Call.objects.filter(
            user=user,
            created_at__date__gte=week_start
        ).count()
        
        weekly_successful = Call.objects.filter(
            user=user,
            created_at__date__gte=week_start,
            status=CallStatus.COMPLETED
        ).count()
        
        # Monthly stats
        month_start = today.replace(day=1)
        monthly_calls = Call.objects.filter(
            user=user,
            created_at__date__gte=month_start
        ).count()
        
        monthly_successful = Call.objects.filter(
            user=user,
            created_at__date__gte=month_start,
            status=CallStatus.COMPLETED
        ).count()
        
        # Average call duration
        avg_duration = Call.objects.filter(
            user=user,
            status=CallStatus.COMPLETED
        ).aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
        
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
            },
            'average_call_duration': round(avg_duration, 2)
        }
        
        return Response(data)
    
    def call_status_distribution(self, request):
        """Get call status distribution"""
        user = request.user
        status_counts = Call.objects.filter(user=user).values('status').annotate(
            count=Count('id')
        )
        
        data = {}
        for item in status_counts:
            data[item['status']] = item['count']
        
        return Response(data)
    
    def top_performing_agents(self, request):
        """Get top performing agents"""
        from apps.account.models import User
        
        # Get users with sells or manager role
        agents = User.objects.filter(
            user_type__in=['sells', 'manager', 'marketing']
        )
        
        agent_performance = []
        for agent in agents:
            total_calls = Call.objects.filter(user=agent).count()
            successful_calls = Call.objects.filter(
                user=agent, 
                status=CallStatus.COMPLETED
            ).count()
            
            avg_duration = Call.objects.filter(
                user=agent,
                status=CallStatus.COMPLETED
            ).aggregate(Avg('duration_seconds'))['duration_seconds__avg'] or 0
            
            agent_performance.append({
                'id': agent.id,
                'name': agent.name or agent.email,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                'average_call_duration': round(avg_duration, 2)
            })
        
        # Sort by successful calls
        agent_performance.sort(key=lambda x: x['successful_calls'], reverse=True)
        
        return Response(agent_performance[:10])

    def overview(self, request):
        """Get complete overview payload for saler dashboard page."""
        user = request.user
        today = timezone.localdate()
        date_from = self._parse_date(request.query_params.get('date_from'))
        date_to = self._parse_date(request.query_params.get('date_to'))
        lead_type = request.query_params.get('lead_type')

        user_leads = Lead.objects.filter(
            Q(assigned_to=user)
            | Q(contact__created_by=user)
            | Q(campaign__created_by=user)
        ).select_related('contact').distinct()

        # Sales overview cards
        prompt_adherence = self._get_prompt_adherence_percentage(user)
        team_prompt_adherence = self._get_team_prompt_adherence_percentage()
        deviation = round(max(0.0, 100.0 - prompt_adherence), 2)

        total_leads = user_leads.count()
        converted_leads = user_leads.filter(status=LeadStatus.CONVERTED).count()
        lead_to_subscription = round((converted_leads / total_leads * 100) if total_leads else 0.0, 2)

        current_target = Target.objects.filter(
            user=user,
            period_start__lte=today,
            period_end__gte=today,
        ).order_by('-period_end').first()
        quota_progress = round(float(current_target.call_progress), 2) if current_target else 0.0

        # Week-over-week change for lead to subscription
        this_week_start = today - timedelta(days=today.weekday())
        last_week_start = this_week_start - timedelta(days=7)
        this_week_end = this_week_start + timedelta(days=6)
        last_week_end = last_week_start + timedelta(days=6)

        this_week_leads = user_leads.filter(created_at__date__range=(this_week_start, this_week_end))
        last_week_leads = user_leads.filter(created_at__date__range=(last_week_start, last_week_end))

        this_week_rate = self._calculate_conversion_rate(this_week_leads)
        last_week_rate = self._calculate_conversion_rate(last_week_leads)
        lead_conversion_change = round(this_week_rate - last_week_rate, 2)

        # Performance analytics (Mon-Sun)
        performance_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        week_dates = [this_week_start + timedelta(days=i) for i in range(7)]
        performance_adherence = [self._get_prompt_adherence_percentage(user, day) for day in week_dates]
        performance_team_avg = [self._get_team_prompt_adherence_percentage(day) for day in week_dates]
        performance_industry_avg = [80.0 for _ in week_dates]

        # New leads today list
        new_leads_today = self._build_new_leads_today(user, today)

        # Conversion rate trend (last 6 months)
        conversion_labels, conversion_values = self._build_conversion_trend(user_leads, today)

        # Call history table
        call_history = self._build_call_history(user, user_leads, date_from=date_from, date_to=date_to, lead_type=lead_type)

        # Active leads table
        active_leads = self._build_active_leads(user_leads, lead_type=lead_type)

        data = {
            'sales_overview': {
                'prompt_adherence': {
                    'value': prompt_adherence,
                    'change': round(prompt_adherence - team_prompt_adherence, 2),
                    'team_avg': team_prompt_adherence,
                    'industry_avg': 80.0,
                },
                'deviation': {
                    'value': deviation,
                    'min': 0,
                    'max': 100,
                    'team_avg': team_prompt_adherence,
                    'industry_avg': 80.0,
                },
                'lead_to_subscription': {
                    'value': lead_to_subscription,
                    'change': lead_conversion_change,
                    'period': 'This week',
                },
                'quota_progress': {
                    'value': quota_progress,
                    'min': 0,
                    'max': 100,
                    'team_avg': team_prompt_adherence,
                    'industry_avg': 80.0,
                },
            },
            'performance_analytics': {
                'labels': performance_labels,
                'adherence': performance_adherence,
                'team_avg': performance_team_avg,
                'industry_avg': performance_industry_avg,
            },
            'new_leads_today': new_leads_today,
            'conversion_rate': {
                'labels': conversion_labels,
                'values': conversion_values,
            },
            'filters_applied': {
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None,
                'lead_type': lead_type,
            },
            'call_history': call_history,
            'active_leads': active_leads,
        }

        return Response(data)

    def sales_overview(self, request):
        """Return only the top sales summary cards."""
        user = request.user
        today = timezone.localdate()
        user_leads = self._get_user_leads_queryset(user)

        prompt_adherence = self._get_prompt_adherence_percentage(user)
        team_prompt_adherence = self._get_team_prompt_adherence_percentage()
        total_leads = user_leads.count()
        converted_leads = user_leads.filter(status=LeadStatus.CONVERTED).count()
        current_target = Target.objects.filter(
            user=user,
            period_start__lte=today,
            period_end__gte=today,
        ).order_by('-period_end').first()

        response = {
            'prompt_adherence': {
                'value': prompt_adherence,
                'change': round(prompt_adherence - team_prompt_adherence, 2),
                'team_avg': team_prompt_adherence,
                'industry_avg': 80.0,
            },
            'deviation': {
                'value': round(max(0.0, 100.0 - prompt_adherence), 2),
                'team_avg': team_prompt_adherence,
                'industry_avg': 80.0,
            },
            'lead_to_subscription': {
                'value': round((converted_leads / total_leads * 100) if total_leads else 0.0, 2),
                'period': 'This week',
            },
            'quota_progress': {
                'value': round(float(current_target.call_progress), 2) if current_target else 0.0,
                'team_avg': team_prompt_adherence,
                'industry_avg': 80.0,
            },
        }
        return Response(response)

    def performance_analytics(self, request):
        """Return the performance analytics chart data."""
        user = request.user
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        week_dates = [week_start + timedelta(days=i) for i in range(7)]

        response = {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'adherence': [self._get_prompt_adherence_percentage(user, day) for day in week_dates],
            'team_avg': [self._get_team_prompt_adherence_percentage(day) for day in week_dates],
            'industry_avg': [80.0 for _ in week_dates],
        }
        return Response(response)

    def lead_insights(self, request):
        """Return new leads today plus conversion trend data."""
        user = request.user
        today = timezone.localdate()
        user_leads = self._get_user_leads_queryset(user)

        response = {
            'new_leads_today': self._build_new_leads_today(user, today),
            'conversion_rate': {
                'labels': self._build_conversion_trend(user_leads, today)[0],
                'values': self._build_conversion_trend(user_leads, today)[1],
            },
        }
        return Response(response)

    def call_history(self, request):
        """Return call history table data."""
        user = request.user
        user_leads = self._get_user_leads_queryset(user)
        date_from = self._parse_date(request.query_params.get('date_from'))
        date_to = self._parse_date(request.query_params.get('date_to'))
        lead_type = request.query_params.get('lead_type')
        response = {
            'filters_applied': {
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None,
                'lead_type': lead_type,
            },
            'results': self._build_call_history(
                user,
                user_leads,
                date_from=date_from,
                date_to=date_to,
                lead_type=lead_type,
            ),
        }
        return Response(response)

    def active_leads(self, request):
        """Return active leads table data."""
        user = request.user
        user_leads = self._get_user_leads_queryset(user)
        lead_type = request.query_params.get('lead_type')
        response = {
            'filters_applied': {
                'lead_type': lead_type,
            },
            'results': self._build_active_leads(user_leads, lead_type=lead_type),
        }
        return Response(response)

    def _calculate_conversion_rate(self, leads_queryset):
        total = leads_queryset.count()
        if not total:
            return 0.0
        converted = leads_queryset.filter(status=LeadStatus.CONVERTED).count()
        return round((converted / total) * 100, 2)

    def _get_user_leads_queryset(self, user):
        return Lead.objects.filter(
            Q(assigned_to=user)
            | Q(contact__created_by=user)
            | Q(campaign__created_by=user)
        ).select_related('contact').distinct()

    def _get_prompt_adherence_percentage(self, user, day=None):
        transcripts = CallTranscript.objects.filter(
            call__user=user,
            role=TranscriptRole.CALLER,
            ai_used_percentage__isnull=False,
        )
        if day is not None:
            transcripts = transcripts.filter(call__created_at__date=day)
        avg_value = transcripts.aggregate(value=Avg('ai_used_percentage'))['value']
        return round(float((avg_value or 0) * 100), 2)

    def _get_team_prompt_adherence_percentage(self, day=None):
        transcripts = CallTranscript.objects.filter(
            call__user__user_type=UserType.SELLS,
            role=TranscriptRole.CALLER,
            ai_used_percentage__isnull=False,
        )
        if day is not None:
            transcripts = transcripts.filter(call__created_at__date=day)
        avg_value = transcripts.aggregate(value=Avg('ai_used_percentage'))['value']
        return round(float((avg_value or 0) * 100), 2)

    def _build_new_leads_today(self, user, today):
        calls_today = Call.objects.filter(user=user, created_at__date=today)
        lead_numbers = calls_today.values('customer_number').annotate(total_calls=Count('id')).order_by('-total_calls')[:4]

        numbers = [item['customer_number'] for item in lead_numbers]
        contacts = Contact.objects.filter(phone_number__in=numbers)
        contacts_map = {contact.phone_number: contact for contact in contacts}

        rows = []
        for item in lead_numbers:
            phone = item['customer_number']
            contact = contacts_map.get(phone)

            adherence_avg = CallTranscript.objects.filter(
                call__user=user,
                call__customer_number=phone,
                role=TranscriptRole.CALLER,
                ai_used_percentage__isnull=False,
            ).aggregate(value=Avg('ai_used_percentage'))['value'] or 0

            rows.append({
                'lead_name': contact.name if contact else phone,
                'company': contact.company if contact and contact.company else None,
                'calls': item['total_calls'],
                'adherence': round(float(adherence_avg) * 100, 2),
            })

        return rows

    def _build_conversion_trend(self, user_leads, today):
        labels = []
        values = []

        # Last 6 months including current month
        for month_offset in range(5, -1, -1):
            anchor = today.replace(day=1)
            month = anchor.month - month_offset
            year = anchor.year

            while month <= 0:
                month += 12
                year -= 1

            while month > 12:
                month -= 12
                year += 1

            month_start = today.replace(year=year, month=month, day=1)
            _, last_day = calendar.monthrange(year, month)
            month_end = today.replace(year=year, month=month, day=last_day)

            month_leads = user_leads.filter(created_at__date__range=(month_start, month_end))
            labels.append(calendar.month_abbr[month])
            values.append(self._calculate_conversion_rate(month_leads))

        return labels, values

    def _build_call_history(self, user, user_leads, date_from=None, date_to=None, lead_type=None):
        calls = Call.objects.filter(user=user)
        if date_from:
            calls = calls.filter(created_at__date__gte=date_from)
        if date_to:
            calls = calls.filter(created_at__date__lte=date_to)
        calls = calls.order_by('-created_at')[:8]
        phones = [call.customer_number for call in calls]

        contacts_map = {
            contact.phone_number: contact
            for contact in Contact.objects.filter(phone_number__in=phones)
        }
        lead_map = {}
        for lead in user_leads.filter(contact__phone_number__in=phones).order_by('-updated_at'):
            if lead_type and lead.status != lead_type:
                continue
            lead_map.setdefault(lead.contact.phone_number, lead)

        rows = []
        for call in calls:
            contact = contacts_map.get(call.customer_number)
            lead = lead_map.get(call.customer_number)
            if lead_type and lead is None:
                continue

            rows.append({
                'call_id': call.id,
                'datetime': timezone.localtime(call.created_at).strftime('%Y-%m-%d %I:%M %p'),
                'lead_name': contact.name if contact else call.customer_number,
                'company': contact.company if contact else None,
                'duration': self._format_duration(call.duration_seconds),
                'follow_up_status': self._map_follow_up_status(lead.status if lead else None),
                'notes_preview': self._truncate_text((lead.notes if lead and lead.notes else ''), 70),
                'report_available': hasattr(call, 'report'),
                'action': 'AI Report',
            })

        return rows

    def _build_active_leads(self, user_leads, lead_type=None):
        active_statuses = [
            LeadStatus.NEW,
            LeadStatus.CONTACTED,
            LeadStatus.INTERESTED,
            LeadStatus.FOLLOW_UP,
        ]

        leads = user_leads.filter(status__in=active_statuses)
        if lead_type:
            leads = leads.filter(status=lead_type)
        leads = leads.order_by('-updated_at')[:10]
        phone_numbers = [lead.contact.phone_number for lead in leads]

        last_calls = {
            item['customer_number']: item['last_contact']
            for item in Call.objects.filter(customer_number__in=phone_numbers)
            .values('customer_number')
            .annotate(last_contact=Max('created_at'))
        }

        rows = []
        for lead in leads:
            last_contact_dt = last_calls.get(lead.contact.phone_number)
            rows.append({
                'lead_id': str(lead.id),
                'lead_name': lead.contact.name,
                'company': lead.contact.company,
                'status': self._map_active_status_label(lead.status),
                'priority': self._map_priority(lead.status),
                'next_action': self._map_next_action(lead.status),
                'last_contact': self._humanize_datetime(last_contact_dt),
            })

        return rows

    def _format_duration(self, seconds):
        total_seconds = int(seconds or 0)
        minutes = total_seconds // 60
        remainder = total_seconds % 60
        return f'{minutes:02}:{remainder:02}'

    def _truncate_text(self, text, length):
        if not text:
            return ''
        return text if len(text) <= length else f'{text[:length - 3]}...'

    def _map_follow_up_status(self, lead_status):
        mapping = {
            LeadStatus.FOLLOW_UP: 'Scheduled Follow-up',
            LeadStatus.CONTACTED: 'Call Back',
            LeadStatus.CONVERTED: 'Completed',
            LeadStatus.INTERESTED: 'Qualified',
            LeadStatus.NEW: 'New Lead',
            LeadStatus.NOT_INTERESTED: 'Dropped',
        }
        return mapping.get(lead_status, 'Pending')

    def _map_active_status_label(self, lead_status):
        mapping = {
            LeadStatus.FOLLOW_UP: 'In Progress',
            LeadStatus.CONTACTED: 'In Progress',
            LeadStatus.INTERESTED: 'Qualified',
            LeadStatus.NEW: 'New lead',
        }
        return mapping.get(lead_status, 'In Progress')

    def _map_priority(self, lead_status):
        if lead_status == LeadStatus.FOLLOW_UP:
            return 'high'
        if lead_status == LeadStatus.INTERESTED:
            return 'medium'
        return 'low'

    def _map_next_action(self, lead_status):
        mapping = {
            LeadStatus.FOLLOW_UP: 'Follow-up Call',
            LeadStatus.CONTACTED: 'Second Outreach',
            LeadStatus.INTERESTED: 'Proposal Review',
            LeadStatus.NEW: 'Initial Meeting',
        }
        return mapping.get(lead_status, 'Follow-up Call')

    def _humanize_datetime(self, dt):
        if not dt:
            return None
        now = timezone.now()
        delta = now - dt
        if delta.days >= 1:
            return f'{delta.days}d ago'
        hours = delta.seconds // 3600
        if hours >= 1:
            return f'{hours}h ago'
        minutes = delta.seconds // 60
        if minutes >= 1:
            return f'{minutes}m ago'
        return 'Just now'

    def _parse_date(self, date_string):
        if not date_string:
            return None
        try:
            return timezone.datetime.fromisoformat(date_string).date()
        except ValueError:
            return None


# ─────────────────────────────────────────────
#          CALIBRATION VIEWS
# ─────────────────────────────────────────────

class CalibrationViewSet(viewsets.ViewSet):
    """
    All calibration endpoints for seller training.

    Flow:
      1.  GET  /calibration/audios/            → list 7 audios
      2.  GET  /calibration/audios/{id}/text/  → reference text (called after audio ends)
      3.  POST /calibration/sessions/          → start new session
      4.  POST /calibration/attempts/          → upload recording (triggers Groq AI)
      5.  GET  /calibration/sessions/{id}/     → session detail + all attempt results
      6.  GET  /calibration/history/           → seller’s past sessions
    """
    permission_classes = [IsAuthenticated]

    # ── 1. List all active calibration audios ───────────────────────────────
    def list_audios(self, request):
        audios = CalibrationAudio.objects.filter(is_active=True)
        serializer = CalibrationAudioSerializer(audios, many=True, context={'request': request})
        return Response(serializer.data)

    # ── 2. Get reference text for ONE audio (called after seller finishes listening) ──
    def audio_text(self, request, pk=None):
        try:
            audio = CalibrationAudio.objects.get(pk=pk, is_active=True)
        except CalibrationAudio.DoesNotExist:
            return Response({'error': 'Audio not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CalibrationAudioDetailSerializer(audio, context={'request': request})
        return Response(serializer.data)

    # ── 3. Start a new calibration session ──────────────────────────────────
    def create_session(self, request):
        session = CalibrationSession.objects.create(seller=request.user)
        serializer = CalibrationSessionSerializer(session, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ── 4. Upload seller recording → trigger AI analysis ───────────────────────
    def submit_recording(self, request):
        upload_serializer = CalibrationAttemptUploadSerializer(data=request.data)
        if not upload_serializer.is_valid():
            return Response(upload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Validate session belongs to requesting user
        session = upload_serializer.validated_data['session']
        if session.seller != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        attempt = upload_serializer.save()

        # Trigger Groq AI analysis
        try:
            result = self._run_ai_analysis(attempt)
            # Update attempt with results
            attempt.transcribed_text = result.get('transcribed_text', '')
            attempt.accuracy_score   = result.get('accuracy_score')
            attempt.fluency_score    = result.get('fluency_score')
            attempt.confidence_score = result.get('confidence_score')
            attempt.overall_score    = result.get('overall_score')
            attempt.ai_feedback      = result.get('ai_feedback')
            attempt.is_analyzed      = True
            attempt.save()

            # Update session overall score
            self._update_session_score(session)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            # Save attempt even if AI fails – can retry later
            attempt.ai_feedback = {'error': str(exc)}
            attempt.save()

        result_serializer = CalibrationAttemptSerializer(attempt, context={'request': request})
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

    # ── 5. Get single session detail ───────────────────────────────────
    def session_detail(self, request, pk=None):
        try:
            session = CalibrationSession.objects.get(pk=pk, seller=request.user)
        except CalibrationSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CalibrationSessionSerializer(session, context={'request': request})
        return Response(serializer.data)

    # ── 6. Seller’s training history ────────────────────────────────────
    def history(self, request):
        sessions = CalibrationSession.objects.filter(seller=request.user)
        serializer = CalibrationSessionSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)

    # ── Internal: run Groq AI analysis ─────────────────────────────────
    def _run_ai_analysis(self, attempt: CalibrationAttempt) -> dict:
        import os
        from groq import Groq
        import json

        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        reference_text = attempt.reference_text.reference_text if attempt.reference_text else ""

        # — Step 1: Transcribe seller’s recording with Groq Whisper —
        recording_path = attempt.recording_file.path
        with open(recording_path, 'rb') as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                model='whisper-large-v3',
                file=audio_file,
                response_format='text',
            )
        transcribed_text = transcription if isinstance(transcription, str) else transcription.text

        # — Step 2: Score with Groq LLaMA 3.3 70B —
        prompt = f"""You are a professional speech coach and sales trainer.
A seller was asked to read and record the following REFERENCE TEXT aloud:

--- REFERENCE TEXT ---
{reference_text}

--- SELLER'S ACTUAL SPEECH (transcribed) ---
{transcribed_text}

Analyze the seller's performance and return ONLY valid JSON with this structure:
{{
  "accuracy_score": <integer 0-100>,
  "fluency_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "overall_score": <integer 0-100>,
  "missing_words": [<list of key words/phrases from reference that seller missed>],
  "extra_words": [<words seller said that were not in reference>],
  "strengths": [<1-3 positive observations>],
  "improvements": [<1-3 specific improvement suggestions>],
  "summary": "<2-3 sentence summary of the seller's performance>"
}}

Scoring guide:
- accuracy_score: how closely seller’s words match the reference text (word-for-word accuracy)
- fluency_score: natural flow, rhythm, no excessive pauses or fillers
- confidence_score: assertive delivery, no hesitation words (um, uh, like)
- overall_score: weighted average (accuracy 40%, fluency 30%, confidence 30%)

Return ONLY the JSON object, no extra text."""

        chat_response = groq_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2,
            max_tokens=800,
        )
        raw = chat_response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            ai_data = json.loads(raw)
        except json.JSONDecodeError:
            # fallback: extract JSON block
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            ai_data = json.loads(match.group()) if match else {}

        return {
            'transcribed_text': transcribed_text,
            'accuracy_score':   ai_data.get('accuracy_score'),
            'fluency_score':    ai_data.get('fluency_score'),
            'confidence_score': ai_data.get('confidence_score'),
            'overall_score':    ai_data.get('overall_score'),
            'ai_feedback':      ai_data,
        }

    # ── Internal: recalculate session average score ──────────────────────
    def _update_session_score(self, session: CalibrationSession):
        from django.utils import timezone as tz
        analyzed = session.attempts.filter(is_analyzed=True)
        total_active = CalibrationAudio.objects.filter(is_active=True).count()

        if analyzed.exists():
            scores = [a.overall_score for a in analyzed if a.overall_score is not None]
            session.overall_score = sum(scores) / len(scores) if scores else None

        if analyzed.count() >= total_active:
            session.is_completed = True
            session.completed_at = tz.now()

        session.save()
