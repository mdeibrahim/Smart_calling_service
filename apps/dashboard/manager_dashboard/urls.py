from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ManagerCampaignViewSet, AllCampaignViewSet, AllContactViewSet,
    AllLeadViewSet, ManagerTargetViewSet, AllTargetViewSet,
    ManagerDashboardViewSet
)

router = DefaultRouter()
router.register(r'campaigns', ManagerCampaignViewSet, basename='manager-campaign')
router.register(r'all-campaigns', AllCampaignViewSet, basename='all-campaign')
router.register(r'contacts', AllContactViewSet, basename='manager-contact')
router.register(r'leads', AllLeadViewSet, basename='manager-lead')
router.register(r'targets', ManagerTargetViewSet, basename='manager-target')
router.register(r'all-targets', AllTargetViewSet, basename='all-target')

urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/stats/', ManagerDashboardViewSet.as_view({'get': 'stats'}), name='manager-dashboard-stats'),
    path('dashboard/recent-calls/', ManagerDashboardViewSet.as_view({'get': 'recent_calls'}), name='manager-dashboard-recent-calls'),
    path('dashboard/campaigns/', ManagerDashboardViewSet.as_view({'get': 'campaigns'}), name='manager-dashboard-campaigns'),
    path('dashboard/contacts/', ManagerDashboardViewSet.as_view({'get': 'contacts'}), name='manager-dashboard-contacts'),
    path('dashboard/leads/', ManagerDashboardViewSet.as_view({'get': 'leads'}), name='manager-dashboard-leads'),
    path('dashboard/targets/', ManagerDashboardViewSet.as_view({'get': 'targets'}), name='manager-dashboard-targets'),
    path('dashboard/performance/', ManagerDashboardViewSet.as_view({'get': 'performance'}), name='manager-dashboard-performance'),
    path('dashboard/call-status/', ManagerDashboardViewSet.as_view({'get': 'call_status_distribution'}), name='manager-dashboard-call-status'),
    path('dashboard/top-agents/', ManagerDashboardViewSet.as_view({'get': 'top_performing_agents'}), name='manager-dashboard-top-agents'),
    path('dashboard/campaign-stats/', ManagerDashboardViewSet.as_view({'get': 'campaign_stats'}), name='manager-dashboard-campaign-stats'),
    path('dashboard/agents/', ManagerDashboardViewSet.as_view({'get': 'agents'}), name='manager-dashboard-agents'),
    path('dashboard/lead-status/', ManagerDashboardViewSet.as_view({'get': 'lead_status_distribution'}), name='manager-dashboard-lead-status'),
    path('dashboard/daily-performance/', ManagerDashboardViewSet.as_view({'get': 'daily_performance'}), name='manager-dashboard-daily-performance'),
]
