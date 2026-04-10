from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.dashboard.support_dashboard.views import SupportTicketViewSet, CallLogViewSet


app_name = 'support_dashboard'

router = DefaultRouter()
router.register(r'tickets', SupportTicketViewSet, basename='support-ticket')
router.register(r'call-logs', CallLogViewSet, basename='call-log')

urlpatterns = [
    path('', include(router.urls)),
]
