from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminCampaignViewSet, AdminTargetViewSet, SystemSettingsViewSet,
    AuditLogViewSet, AllCampaignViewSet, AllContactViewSet,
    AllLeadViewSet, AllTargetViewSet, AdminDashboardViewSet,
    UserManagementViewSet
)

router = DefaultRouter()
router.register(r'campaigns', AdminCampaignViewSet, basename='admin-campaigns')
router.register(r'targets', AdminTargetViewSet, basename='admin-targets')
router.register(r'settings', SystemSettingsViewSet, basename='system-settings')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-logs')
router.register(r'all-campaigns', AllCampaignViewSet, basename='all-campaigns')
router.register(r'all-contacts', AllContactViewSet, basename='all-contacts')
router.register(r'all-leads', AllLeadViewSet, basename='all-leads')
router.register(r'all-targets', AllTargetViewSet, basename='all-targets')
router.register(r'users', UserManagementViewSet, basename='user-management')

urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/stats/', AdminDashboardViewSet.as_view({'get': 'stats'}), name='dashboard-stats'),
    path('dashboard/recent-calls/', AdminDashboardViewSet.as_view({'get': 'recent_calls'}), name='dashboard-recent-calls'),
    path('dashboard/campaigns/', AdminDashboardViewSet.as_view({'get': 'campaigns'}), name='dashboard-campaigns'),
    path('dashboard/contacts/', AdminDashboardViewSet.as_view({'get': 'contacts'}), name='dashboard-contacts'),
    path('dashboard/leads/', AdminDashboardViewSet.as_view({'get': 'leads'}), name='dashboard-leads'),
    path('dashboard/targets/', AdminDashboardViewSet.as_view({'get': 'targets'}), name='dashboard-targets'),
    path('dashboard/performance/', AdminDashboardViewSet.as_view({'get': 'performance'}), name='dashboard-performance'),
    path('dashboard/call-status-distribution/', AdminDashboardViewSet.as_view({'get': 'call_status_distribution'}), name='dashboard-call-status'),
    path('dashboard/top-agents/', AdminDashboardViewSet.as_view({'get': 'top_performing_agents'}), name='dashboard-top-agents'),
    path('dashboard/campaign-stats/', AdminDashboardViewSet.as_view({'get': 'campaign_stats'}), name='dashboard-campaign-stats'),
    path('dashboard/users/', AdminDashboardViewSet.as_view({'get': 'users'}), name='dashboard-users'),
    path('dashboard/lead-status-distribution/', AdminDashboardViewSet.as_view({'get': 'lead_status_distribution'}), name='dashboard-lead-status'),
    path('dashboard/daily-performance/', AdminDashboardViewSet.as_view({'get': 'daily_performance'}), name='dashboard-daily-performance'),
    
    # User management endpoints
    path('users/list/', UserManagementViewSet.as_view({'get': 'list_users'}), name='user-list'),
    path('users/agents/', UserManagementViewSet.as_view({'get': 'agents'}), name='user-agents'),
    path('users/managers/', UserManagementViewSet.as_view({'get': 'managers'}), name='user-managers'),
]
