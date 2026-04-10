from rest_framework import serializers
from .models import Campaign, Contact, Lead, Target, CalibrationAudio, CalibrationSession, CalibrationAttempt
from apps.calling.models import Call


class CampaignSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    leads_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'status', 'created_by', 'created_by_name',
            'start_date', 'end_date', 'target_calls', 'leads_count', 'created_at', 'updated_at'
        ]
    
    def get_leads_count(self, obj):
        return obj.leads.count()


class ContactSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'phone_number', 'email', 'company', 'address',
            'notes', 'created_by', 'created_by_name', 'created_at', 'updated_at'
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
    unique_leads = serializers.IntegerField()
    total_call_duration = serializers.IntegerField()
    average_call_duration = serializers.FloatField()
    success_rate = serializers.FloatField()


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


# ─────────────────────────────────────────────
#         CALIBRATION SERIALIZERS
# ─────────────────────────────────────────────

class CalibrationAudioSerializer(serializers.ModelSerializer):
    """Returned when listing all 7 audios (no reference_text exposed until audio ends)."""
    audio_url = serializers.SerializerMethodField()

    class Meta:
        model = CalibrationAudio
        fields = ['id', 'title', 'description', 'audio_url', 'order', 'is_active']

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None


class CalibrationAudioDetailSerializer(serializers.ModelSerializer):
    """Returned after seller finishes listening — includes a random reference_text."""
    audio_url = serializers.SerializerMethodField()
    reference_text = serializers.SerializerMethodField()

    class Meta:
        model = CalibrationAudio
        fields = ['id', 'title', 'description', 'audio_url', 'reference_text', 'order']

    def get_reference_text(self, obj):
        import random
        texts = obj.reference_texts.all()
        if texts.exists():
            selected = random.choice(list(texts))
            return {
                "id": selected.id,
                "text_defficulty": selected.text_defficulty,
                "text": selected.reference_text
            }
        return None

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None


class CalibrationAttemptSerializer(serializers.ModelSerializer):
    audio_title = serializers.CharField(source='audio.title', read_only=True)
    audio_order = serializers.IntegerField(source='audio.order', read_only=True)

    class Meta:
        model = CalibrationAttempt
        fields = [
            'id', 'session', 'audio', 'audio_title', 'audio_order',
            'recording_file',
            'transcribed_text', 'accuracy_score', 'fluency_score',
            'confidence_score', 'overall_score', 'ai_feedback',
            'is_analyzed', 'created_at',
        ]
        read_only_fields = [
            'transcribed_text', 'accuracy_score', 'fluency_score',
            'confidence_score', 'overall_score', 'ai_feedback', 'is_analyzed',
        ]


class CalibrationAttemptUploadSerializer(serializers.ModelSerializer):
    """Used when seller submits a recording."""

    class Meta:
        model = CalibrationAttempt
        fields = ['session', 'audio', 'reference_text', 'recording_file']


class CalibrationSessionSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.name', read_only=True)
    attempts = CalibrationAttemptSerializer(many=True, read_only=True)
    total_audios = serializers.SerializerMethodField()
    completed_audios = serializers.SerializerMethodField()

    class Meta:
        model = CalibrationSession
        fields = [
            'id', 'seller', 'seller_name', 'started_at', 'completed_at',
            'is_completed', 'overall_score',
            'total_audios', 'completed_audios', 'attempts',
        ]
        read_only_fields = ['seller', 'overall_score', 'completed_at', 'is_completed']

    def get_total_audios(self, obj):
        return CalibrationAudio.objects.filter(is_active=True).count()

    def get_completed_audios(self, obj):
        return obj.attempts.filter(is_analyzed=True).count()
