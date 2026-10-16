from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from groups.models import Group, GroupMember


class GroupCreationTest(APITestCase):
    def setUp(self):
        self.create_url = reverse("group-create")
        self.data = {"email": "testuser@mail.com", "username": "testuser1234", "password": "R286rn5fAWsf"}
        self.user = get_user_model().objects.create_user(
            email=self.data["email"], username=self.data["username"], password=self.data["password"]
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.user)}")

    def test_create_group_proper(self):
        response = self.client.post(self.create_url, {"name": "TestGroup"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        self.assertEqual(GroupMember.objects.count(), 1)
        self.assertTrue(GroupMember.objects.filter(user=self.user, group_id=response.data["id"]).exists())
        self.assertIn("id", response.data)
        self.assertIn("owner", response.data)
        self.assertIn("invite_id", response.data)
        self.assertIn("created_at", response.data)
        self.assertEqual(response.data["owner"], self.user.id)

    def test_create_group_unauthorized(self):
        self.client.credentials()
        response = self.client.post(self.create_url, {"name": "TestGroup"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"].code, "not_authenticated")
        self.assertEqual(Group.objects.count(), 0)
        self.assertEqual(GroupMember.objects.count(), 0)
        self.assertNotIn("id", response.data)
        self.assertNotIn("owner", response.data)
        self.assertNotIn("invite_id", response.data)
        self.assertNotIn("created_at", response.data)

    def test_create_group_empty_request(self):
        response = self.client.post(self.create_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertEqual(Group.objects.count(), 0)
        self.assertEqual(GroupMember.objects.count(), 0)

    def test_create_group_forge_owner(self):
        malicious_user = get_user_model().objects.create_user(
            email="malicioususer@test.com", username="MalUser", password="R286rn5fAWsfm"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(malicious_user)}")
        response = self.client.post(self.create_url, {"name": "TestGroup", "owner": str(self.user.id)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        self.assertEqual(GroupMember.objects.count(), 1)
        self.assertTrue(GroupMember.objects.filter(user=malicious_user).exists())
        self.assertIn("id", response.data)
        self.assertIn("owner", response.data)
        self.assertIn("invite_id", response.data)
        self.assertIn("created_at", response.data)
        self.assertEqual(response.data["owner"], malicious_user.id)
