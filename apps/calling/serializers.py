from rest_framework import serializers
from .models import Call, CallTranscript, CallReport


class CallTranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallTranscript
        fields = [
            'id', 'call', 'role', 'content', 'timestamp',
            'ai_used_percentage', 'created_at',
        ]


class CallReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallReport
        fields = [
            'id', 'call', 'report_data', 'performance_score',
            'call_status', 'created_at',
        ]


class CallSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Call
        fields = [
            'id', 'user', 'user_name', 'seller_number', 'customer_number',
            'twilio_call_sid', 'status', 'status_display',
            'started_at', 'ended_at', 'duration_seconds',
            'created_at', 'updated_at',
        ]
