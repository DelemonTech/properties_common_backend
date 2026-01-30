from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import AgentDetails  # adjust as needed
from django.test import TestCase

class AgentViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.agent = AgentDetails.objects.create(
            username=self.user.username,
            name="Test Agent",
            email="test@example.com",
            whatsapp_number="1234567890",
            phone_number="1234567890",
            profile_image_url="http://example.com/image.jpg",
            introduction_video_url="http://example.com/video.mp4",
            description="Experienced agent",
            years_of_experience="5",
            total_business_deals="100",
            rank_top_performing="Top 1%",
            fa_name="FA Group",
            fa_description="Top Real Estate Group"
        )

    def test_agent_detail_by_username(self):
        url = reverse('agent-detail-by-username', args=[self.agent.username])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], self.agent.username)

    def test_register_agent(self):
        url = "/agent/register/"
        payload = {
            "username": "newagent",
            "name": "New Agent",
            "email": "newagent@example.com",
            "whatsapp_number": "9999999999",
            "phone_number": "8888888888",
            "profile_image_url": "http://example.com/new.jpg",
            "introduction_video_url": "http://example.com/newvideo.mp4",
            "description": "New to real estate",
            "years_of_experience": "1",
            "total_business_deals": "5",
            "rank_top_performing": "N/A",
            "fa_name": "New FA",
            "fa_description": "New Description"
        }
        response = self.client.post(url, payload)
        self.assertIn(response.status_code, [200, 201])
        self.assertEqual(response.data['email'], payload['email'])

    def test_update_agent(self):
        url = f"/agent/update/{self.agent.id}/"
        self.client.force_authenticate(user=self.user)
        payload = {
            "name": "Updated Agent",
            "email": "updated@example.com",
            "whatsapp_number": "1111111111",
            "phone_number": "2222222222",
            "profile_image_url": "http://example.com/updated.jpg",
            "introduction_video_url": "http://example.com/updated.mp4",
            "description": "Updated description",
            "years_of_experience": "6",
            "total_business_deals": "120",
            "rank_top_performing": "Top 5%",
            "fa_name": "Updated FA",
            "fa_description": "Updated Description"
        }
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], payload['name'])

    def test_delete_agent(self):
        url = f"/agent/delete/{self.agent.id}/"
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertIn(response.status_code, [200, 204])
        self.assertFalse(AgentDetails.objects.filter(id=self.agent.id).exists())
