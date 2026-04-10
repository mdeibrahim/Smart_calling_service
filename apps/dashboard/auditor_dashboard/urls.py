from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuditorSettingsViewSet, AuditorFilterPresetViewSet,
    AuditorBookmarkViewSet, AuditorCallHistoryViewSet,
    AuditorCallReportsViewSet, AuditorCampaignsViewSet,
    AuditorContactsViewSet, AuditorLeadsViewSet,
    AuditorDashboardViewSet
)

router = DefaultRouter()
router.register(r'settings', AuditorSettingsViewSet, basename='auditor-settings')
router.register(r'filter-presets', AuditorFilterPresetViewSet, basename='auditor-filter-presets')
router.register(r'bookmarks', AuditorBookmarkViewSet, basename='auditor-bookmarks')
router.register(r'calls', AuditorCallHistoryViewSet, basename='auditor-calls')
router.register(r'campaigns', AuditorCampaignsViewSet, basename='auditor-campaigns')
router.register(r'contacts', AuditorContactsViewSet, basename='auditor-contacts')
router.register(r'leads', AuditorLeadsViewSet, basename='auditor-leads')

urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/overview/', AuditorDashboardViewSet.as_view({'get': 'overview'}), name='auditor-dashboard-overview'),
    path('dashboard/recent-calls/', AuditorDashboardViewSet.as_view({'get': 'recent_calls'}), name='auditor-dashboard-recent-calls'),
    path('dashboard/top-agents/', AuditorDashboardViewSet.as_view({'get': 'top_agents'}), name='auditor-dashboard-top-agents'),
    
    # Reports endpoints
    path('reports/stats/', AuditorCallReportsViewSet.as_view({'get': 'stats'}), name='auditor-reports-stats'),
    path('reports/daily/', AuditorCallReportsViewSet.as_view({'get': 'daily_stats'}), name='auditor-reports-daily'),
    path('reports/weekly/', AuditorCallReportsViewSet.as_view({'get': 'weekly_stats'}), name='auditor-reports-weekly'),
    path('reports/monthly/', AuditorCallReportsViewSet.as_view({'get': 'monthly_stats'}), name='auditor-reports-monthly'),
    path('reports/call-status/', AuditorCallReportsViewSet.as_view({'get': 'call_status_distribution'}), name='auditor-reports-call-status'),
    path('reports/agent-performance/', AuditorCallReportsViewSet.as_view({'get': 'agent_performance'}), name='auditor-reports-agent-performance'),
    path('reports/campaign-performance/', AuditorCallReportsViewSet.as_view({'get': 'campaign_performance'}), name='auditor-reports-campaign-performance'),
    path('reports/duration-distribution/', AuditorCallReportsViewSet.as_view({'get': 'duration_distribution'}), name='auditor-reports-duration-distribution'),
]
