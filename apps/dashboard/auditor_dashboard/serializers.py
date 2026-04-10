from rest_framework import serializers
from .models import AuditorSettings, AuditorFilterPreset, AuditorBookmark
from apps.calling.models import Call, CallTranscript, CallReport
from apps.dashboard.saler_dashboard.models import Campaign, Contact, Lead


class AuditorSettingsSerializer(serializers.ModelSerializer):
    """Serializer for auditor settings"""
    
    class Meta:
        model = AuditorSettings
        fields = [
            'id', 'user', 'default_page_size', 'show_transcripts',
            'show_reports', 'email_notifications', 'notification_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AuditorFilterPresetSerializer(serializers.ModelSerializer):
    """Serializer for auditor filter presets"""
    
    class Meta:
        model = AuditorFilterPreset
        fields = [
            'id', 'user', 'name', 'filter_data', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AuditorBookmarkSerializer(serializers.ModelSerializer):
    """Serializer for auditor bookmarks"""
    
    class Meta:
        model = AuditorBookmark
        fields = [
            'id', 'user', 'call_id', 'note', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


# Call History Serializers
class CallTranscriptSerializer(serializers.ModelSerializer):
    """Serializer for call transcripts"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CallTranscript
        fields = [
            'id', 'call', 'role', 'role_display', 'content',
            'timestamp', 'ai_used_percentage', 'created_at'
        ]


class CallReportSerializer(serializers.ModelSerializer):
    """Serializer for call reports"""
    
    class Meta:
        model = CallReport
        fields = [
            'id', 'call', 'report_data', 'performance_score',
            'call_status', 'created_at'
        ]


class AuditorCallListSerializer(serializers.ModelSerializer):
    """Serializer for call list in auditor dashboard"""
    
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_transcript = serializers.SerializerMethodField()
    has_report = serializers.SerializerMethodField()
    
    class Meta:
        model = Call
        fields = [
            'id', 'user', 'user_name', 'user_email', 'seller_number',
            'customer_number', 'status', 'status_display', 'started_at',
            'ended_at', 'duration_seconds', 'twilio_call_sid',
            'has_transcript', 'has_report', 'created_at'
        ]
    
    def get_has_transcript(self, obj):
        return CallTranscript.objects.filter(call=obj).exists()
    
    def get_has_report(self, obj):
        return hasattr(obj, 'report') and obj.report is not None


class AuditorCallDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for call in auditor dashboard"""
    
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transcripts = CallTranscriptSerializer(many=True, read_only=True)
    report = serializers.SerializerMethodField()
    
    class Meta:
        model = Call
        fields = [
            'id', 'user', 'user_name', 'user_email', 'seller_number',
            'customer_number', 'status', 'status_display', 'started_at',
            'ended_at', 'duration_seconds', 'twilio_call_sid',
            'transcripts', 'report', 'created_at', 'updated_at'
        ]
    
    def get_report(self, obj):
        try:
            report = CallReport.objects.get(call=obj)
            return CallReportSerializer(report).data
        except CallReport.DoesNotExist:
            return None


# Campaign Serializers for Auditor
class AuditorCampaignListSerializer(serializers.ModelSerializer):
    """Serializer for campaign list in auditor dashboard"""
    
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    total_contacts = serializers.SerializerMethodField()
    total_leads = serializers.SerializerMethodField()
    converted_leads = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'status', 'created_by',
            'created_by_name', 'start_date', 'end_date', 'target_calls',
            'total_contacts', 'total_leads', 'converted_leads',
            'created_at', 'updated_at'
        ]
    
    def get_total_contacts(self, obj):
        return Contact.objects.filter(campaign=obj).count()
    
    def get_total_leads(self, obj):
        return Lead.objects.filter(campaign=obj).count()
    
    def get_converted_leads(self, obj):
        return Lead.objects.filter(campaign=obj, status='converted').count()


# Contact Serializers for Auditor
class AuditorContactListSerializer(serializers.ModelSerializer):
    """Serializer for contact list in auditor dashboard"""
    
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    total_calls = serializers.SerializerMethodField()
    successful_calls = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone_number', 'email', 'company',
            'address', 'notes', 'created_by', 'created_by_name',
            'campaign', 'campaign_name', 'total_calls', 'successful_calls',
            'created_at', 'updated_at'
        ]
    
    def get_total_calls(self, obj):
        return Call.objects.filter(customer_number=obj.phone_number).count()
    
    def get_successful_calls(self, obj):
        from apps.calling.models import CallStatus
        return Call.objects.filter(
            customer_number=obj.phone_number,
            status=CallStatus.COMPLETED
        ).count()


# Lead Serializers for Auditor
class AuditorLeadListSerializer(serializers.ModelSerializer):
    """Serializer for lead list in auditor dashboard"""
    
    contact_name = serializers.CharField(source='contact.name', read_only=True)
    contact_phone = serializers.CharField(source='contact.phone_number', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    total_calls = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'contact', 'contact_name', 'contact_phone', 'campaign',
            'campaign_name', 'assigned_to', 'assigned_to_name', 'status',
            'value', 'notes', 'created_by', 'created_by_name',
            'total_calls', 'created_at', 'updated_at'
        ]
    
    def get_total_calls(self, obj):
        if obj.contact:
            return Call.objects.filter(customer_number=obj.contact.phone_number).count()
        return 0


# Dashboard Stats Serializer
class AuditorDashboardStatsSerializer(serializers.Serializer):
    """Serializer for auditor dashboard statistics"""
    
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    failed_calls = serializers.IntegerField()
    total_duration = serializers.IntegerField()
    average_duration = serializers.FloatField()
    success_rate = serializers.FloatField()
    total_campaigns = serializers.IntegerField()
    active_campaigns = serializers.IntegerField()
    total_contacts = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    lead_conversion_rate = serializers.FloatField()


# Agent Performance Serializer for Auditor
class AuditorAgentPerformanceSerializer(serializers.Serializer):
    """Serializer for agent performance in auditor dashboard"""
    
    agent_id = serializers.IntegerField()
    agent_name = serializers.CharField()
    agent_email = serializers.EmailField()
    user_type = serializers.CharField()
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    failed_calls = serializers.IntegerField()
    total_duration = serializers.IntegerField()
    average_duration = serializers.FloatField()
    success_rate = serializers.FloatField()
    leads_assigned = serializers.IntegerField()
    converted_leads = serializers.IntegerField()


# Campaign Performance Serializer for Auditor
class AuditorCampaignPerformanceSerializer(serializers.Serializer):
    """Serializer for campaign performance in auditor dashboard"""
    
    campaign_id = serializers.UUIDField()
    campaign_name = serializers.CharField()
    status = serializers.CharField()
    total_contacts = serializers.IntegerField()
    total_calls = serializers.IntegerField()
    successful_calls = serializers.IntegerField()
    failed_calls = serializers.IntegerField()
    total_leads = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    success_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()
