from django.urls import include, path

urlpatterns = [
    path('saler/', include('apps.dashboard.saler_dashboard.urls')),
    path('manager/', include('apps.dashboard.manager_dashboard.urls')),
    path('admin/', include('apps.dashboard.admin_dashboard.urls')),
    path('auditor/', include('apps.dashboard.auditor_dashboard.urls')),
    path('support/', include('apps.dashboard.support_dashboard.urls')),
]