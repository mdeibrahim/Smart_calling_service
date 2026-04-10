from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampaignViewSet, ContactViewSet, LeadViewSet, 
    TargetViewSet, DashboardViewSet, CalibrationViewSet
)

router = DefaultRouter()
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'targets', TargetViewSet, basename='target')

urlpatterns = [
    path('', include(router.urls)),

    # dashboard endpoints
    path('dashboard/overview/', DashboardViewSet.as_view({'get': 'overview'}), name='dashboard-overview'),
    path('dashboard/sales-overview/', DashboardViewSet.as_view({'get': 'sales_overview'}), name='dashboard-sales-overview'),
    path('dashboard/performance-analytics/', DashboardViewSet.as_view({'get': 'performance_analytics'}), name='dashboard-performance-analytics'),
    path('dashboard/lead-insights/', DashboardViewSet.as_view({'get': 'lead_insights'}), name='dashboard-lead-insights'),
    path('dashboard/call-history/', DashboardViewSet.as_view({'get': 'call_history'}), name='dashboard-call-history'),
    path('dashboard/active-leads/', DashboardViewSet.as_view({'get': 'active_leads'}), name='dashboard-active-leads'),


    path('dashboard/stats/', DashboardViewSet.as_view({'get': 'stats'}), name='dashboard-stats'),
    path('dashboard/recent-calls/', DashboardViewSet.as_view({'get': 'recent_calls'}), name='dashboard-recent-calls'),
    path('dashboard/campaigns/', DashboardViewSet.as_view({'get': 'campaigns'}), name='dashboard-campaigns'),
    path('dashboard/contacts/', DashboardViewSet.as_view({'get': 'contacts'}), name='dashboard-contacts'),
    path('dashboard/leads/', DashboardViewSet.as_view({'get': 'leads'}), name='dashboard-leads'),
    path('dashboard/targets/', DashboardViewSet.as_view({'get': 'targets'}), name='dashboard-targets'),
    path('dashboard/performance/', DashboardViewSet.as_view({'get': 'performance'}), name='dashboard-performance'),
    path('dashboard/call-status/', DashboardViewSet.as_view({'get': 'call_status_distribution'}), name='dashboard-call-status'),
    path('dashboard/top-agents/', DashboardViewSet.as_view({'get': 'top_performing_agents'}), name='dashboard-top-agents'),

    

    # ─────────────────────────────────────────
    #   CALIBRATION  endpoints
    # ─────────────────────────────────────────
    # 1. GET  all audios (no text yet)
    path('calibration/audios/', CalibrationViewSet.as_view({'get': 'list_audios'}), name='calibration-audios'),
    # 2. GET  reference text after audio ends
    path('calibration/audios/<int:pk>/text/', CalibrationViewSet.as_view({'get': 'audio_text'}), name='calibration-audio-text'),
    # 3. POST start session
    path('calibration/sessions/', CalibrationViewSet.as_view({'post': 'create_session'}), name='calibration-session-create'),
    # 4. POST upload recording  (triggers Groq AI)
    path('calibration/attempts/', CalibrationViewSet.as_view({'post': 'submit_recording'}), name='calibration-attempt'),
    # 5. GET  single session detail
    path('calibration/sessions/<int:pk>/', CalibrationViewSet.as_view({'get': 'session_detail'}), name='calibration-session-detail'),
    # 6. GET  seller training history
    path('calibration/history/', CalibrationViewSet.as_view({'get': 'history'}), name='calibration-history'),
]
