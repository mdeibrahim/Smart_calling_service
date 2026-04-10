from rest_framework import serializers
from .models import ManagerCampaign, ManagerTarget
from apps.dashboard.saler_dashboard.models import Campaign, Contact, Lead, Target
from apps.calling.models import Call


class ManagerCampaignSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    leads_count = serializers.SerializerMethodField()
    total_calls = serializers.SerializerMethodField()
    successful_calls = serializers.SerializerMethodField()
    
    class Meta:
        model = ManagerCampaign
        fields = [
            'id', 'name', 'description', 'status', 'created_by', 'created_by_name',
            'start_date', 'end_date', 'target_calls', 'leads_count', 
            'total_calls', 'successful_calls',
            'created_at', 'updated_at'
        ]
    
    def get_leads_count(self, obj):
        return Lead.objects.filter(campaign_id=obj.id).count()
    
    def get_total_calls(self, obj):
        # Get calls from contacts in this campaign
        campaign_contacts = Contact.objects.filter(campaign=obj)
        return Call.objects.filter(customer_number__in=campaign_contacts.values_list('phone_number', flat=True)).count()
    
    def get_successful_calls(self, obj):
        from apps.calling.models import CallStatus
        campaign_contacts = Contact.objects.filter(campaign=obj)
        return Call.objects.filter(
            customer_number__in=campaign_contacts.values_list('phone_number', flat=True),
            status=CallStatus.COMPLETED
        ).count()


class ContactSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone_number', 'email', 'company', 'address',
            'notes', 'created_by', 'created_by_name', 'campaign', 'campaign_name',
            'created_at', 'updated_at'
        ]


class LeadSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone_number', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'contact', 'contact_name', 'contact_phone', 'campaign', 'campaign_name',
            'assigned_to', 'assigned_to_name', 'status', 'value', 'notes',
            'created_at', 'updated_at'
        ]


class LeadAssignSerializer(serializers.Serializer):
    lead_id = serializers.UUIDField()
    assigned_to_id = serializers.IntegerField()


class ManagerTargetSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    agent_email = serializers.CharField(source='agent.email', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    call_progress = serializers.ReadOnlyField()
    revenue_progress = serializers.ReadOnlyField()
    
    class Meta:
        model = ManagerTarget
        fields = [
            'id', 'agent', 'agent_name', 'agent_email', 'campaign', 'campaign_name',
            'target_calls', 'achieved_calls', 'target_revenue', 'achieved_revenue',
            'period_start', 'period_end', 'call_progress', 'revenue_progress',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class TargetSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    call_progress = serializers.ReadOnlyField()
    revenue_progress = serializers.ReadOnlyField()
    
    class Meta:
        model = Target
        fields = [
            'id', 'user', 'user_name', 'campaign', 'campaign_name',
            'target_calls', 'achieved_calls', 'target_revenue', 'achieved_revenue',
            'period_start', 'period_end', 'call_progress', 'revenue_progress',
            'created_at', 'updated_at'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    missed_calls = serializers.IntegerField()
    total_agents = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    total_call_duration = serializers.IntegerField()
    average_call_duration = serializers.FloatField()
    success_rate = serializers.FloatField()
    lead_conversion_rate = serializers.FloatField()


class AgentPerformanceSerializer(serializers.Serializer):
    agent_id = serializers.IntegerField()
    agent_name = serializers.CharField()
    agent_email = serializers.EmailField()
    user_type = serializers.CharField()
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    missed_calls = serializers.IntegerField()
    total_duration = serializers.IntegerField()
    average_duration = serializers.FloatField()
    success_rate = serializers.FloatField()
    leads_assigned = serializers.IntegerField()
    leads_converted = serializers.IntegerField()


class CampaignStatsSerializer(serializers.Serializer):
    campaign_id = serializers.UUIDField()
    campaign_name = serializers.CharField()
    status = serializers.CharField()
    total_leads = serializers.IntegerField()
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    success_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()


class CallListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Call
        fields = [
            'id', 'user', 'user_name', 'seller_number', 'customer_number',
            'status', 'status_display', 'started_at', 'ended_at',
            'duration_seconds', 'created_at'
        ]


class AgentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='name', read_only=True)
    
    class Meta:
        model = __import__('apps.account.models', fromlist=['User']).User
        fields = ['id', 'name', 'email', 'phone_number', 'user_type', 'is_active', 'created_at']
