from rest_framework import serializers
from .models import AdminCampaign, AdminTarget, SystemSettings, AuditLog
from apps.dashboard.saler_dashboard.models import Campaign, Contact, Lead, Target
from apps.dashboard.manager_dashboard.models import ManagerCampaign, ManagerTarget
from apps.calling.models import Call


class AdminCampaignSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    leads_count = serializers.SerializerMethodField()
    total_calls = serializers.SerializerMethodField()
    successful_calls = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminCampaign
        fields = [
            'id', 'name', 'description', 'status', 'created_by', 'created_by_name',
            'start_date', 'end_date', 'target_calls', 'priority', 'is_global',
            'leads_count', 'total_calls', 'successful_calls',
            'created_at', 'updated_at'
        ]
    
    def get_leads_count(self, obj):
        return Lead.objects.filter(campaign_id=obj.id).count()
    
    def get_total_calls(self, obj):
        campaign_contacts = Contact.objects.filter(campaign=obj)
        return Call.objects.filter(customer_number__in=campaign_contacts.values_list('phone_number', flat=True)).count()
    
    def get_successful_calls(self, obj):
        from apps.calling.models import CallStatus
        campaign_contacts = Contact.objects.filter(campaign=obj)
        return Call.objects.filter(
            customer_number__in=campaign_contacts.values_list('phone_number', flat=True),
            status=CallStatus.COMPLETED
        ).count()


class AdminTargetSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    call_progress = serializers.ReadOnlyField()
    revenue_progress = serializers.ReadOnlyField()
    
    class Meta:
        model = AdminTarget
        fields = [
            'id', 'user', 'user_name', 'user_email', 'campaign', 'campaign_name',
            'target_calls', 'achieved_calls', 'target_revenue', 'achieved_revenue',
            'period_start', 'period_end', 'call_progress', 'revenue_progress',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class SystemSettingsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = SystemSettings
        fields = [
            'id', 'key', 'value', 'description', 'is_active',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'user_email', 'action', 'model_name',
            'object_id', 'changes', 'ip_address', 'user_agent', 'created_at'
        ]


# Re-use serializers from other dashboards for read operations
class CampaignListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'status', 'created_by', 'created_by_name',
            'start_date', 'end_date', 'target_calls', 'created_at', 'updated_at'
        ]


class ContactListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone_number', 'email', 'company', 'address',
            'notes', 'created_by', 'created_by_name', 'campaign', 'campaign_name',
            'created_at', 'updated_at'
        ]


class LeadListSerializer(serializers.ModelSerializer):
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone_number', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'contact', 'contact_name', 'contact_phone', 'campaign', 'campaign_name',
            'assigned_to', 'assigned_to_name', 'status', 'value', 'notes',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]


class TargetListSerializer(serializers.ModelSerializer):
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


class ManagerTargetListSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    call_progress = serializers.ReadOnlyField()
    revenue_progress = serializers.ReadOnlyField()
    
    class Meta:
        model = ManagerTarget
        fields = [
            'id', 'agent', 'agent_name', 'campaign', 'campaign_name',
            'target_calls', 'achieved_calls', 'target_revenue', 'achieved_revenue',
            'period_start', 'period_end', 'call_progress', 'revenue_progress',
            'created_at', 'updated_at'
        ]


# Dashboard Stats Serializers
class AdminDashboardStatsSerializer(serializers.Serializer):
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    missed_calls = serializers.IntegerField()
    total_agents = serializers.IntegerField()
    total_managers = serializers.IntegerField()
    total_admins = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    total_campaigns = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    total_contacts = serializers.IntegerField()
    total_call_duration = serializers.IntegerField()
    average_call_duration = serializers.FloatField()
    success_rate = serializers.FloatField()
    lead_conversion_rate = serializers.FloatField()


class AdminAgentPerformanceSerializer(serializers.Serializer):
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
    revenue_generated = serializers.FloatField()


class AdminCampaignStatsSerializer(serializers.Serializer):
    campaign_id = serializers.UUIDField()
    campaign_name = serializers.CharField()
    status = serializers.CharField()
    total_leads = serializers.IntegerField()
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    success_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()


class AdminCallListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Call
        fields = [
            'id', 'user', 'user_name', 'seller_number', 'customer_number',
            'status', 'status_display', 'started_at', 'ended_at',
            'duration_seconds', 'created_at'
        ]


class AdminUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    user_type = serializers.CharField()
    is_active = serializers.BooleanField()
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class LeadAssignSerializer(serializers.Serializer):
    lead_id = serializers.UUIDField()
    assigned_to_id = serializers.IntegerField()


class BulkActionSerializer(serializers.Serializer):
    action = serializers.CharField()
    object_ids = serializers.ListField(child=serializers.UUIDField())
    data = serializers.JSONField(required=False)
