from uuid import uuid4

from django.test import TestCase
from rest_framework.test import APIClient

from apps.account.models import User, UserType


class SalerDashboardOverviewApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			email=f'saler_{uuid4().hex[:8]}@test.com',
			password='test12345',
			phone_number='01700000000',
			user_type=UserType.SELLS,
			name='Sales User',
		)
		self.client.force_authenticate(user=self.user)

	def test_sales_overview_endpoint(self):
		response = self.client.get('/api/dashboard/saler/dashboard/sales-overview/')
		self.assertEqual(response.status_code, 200)
		self.assertIn('prompt_adherence', response.data)
		self.assertIn('quota_progress', response.data)

	def test_performance_analytics_endpoint(self):
		response = self.client.get('/api/dashboard/saler/dashboard/performance-analytics/')
		self.assertEqual(response.status_code, 200)
		self.assertIn('labels', response.data)
		self.assertIn('adherence', response.data)

	def test_lead_insights_endpoint(self):
		response = self.client.get('/api/dashboard/saler/dashboard/lead-insights/')
		self.assertEqual(response.status_code, 200)
		self.assertIn('new_leads_today', response.data)
		self.assertIn('conversion_rate', response.data)

	def test_call_history_endpoint(self):
		response = self.client.get('/api/dashboard/saler/dashboard/call-history/')
		self.assertEqual(response.status_code, 200)
		self.assertIn('results', response.data)

	def test_active_leads_endpoint(self):
		response = self.client.get('/api/dashboard/saler/dashboard/active-leads/')
		self.assertEqual(response.status_code, 200)
		self.assertIn('results', response.data)
