import base64
import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


def forge_token(token: str, user_id: int | None = None) -> str:
    token = token.split(".")
    payload = base64.urlsafe_b64decode(token[1] + ("=" * ((4 - (len(token[1]) % 4)) % 4))).decode()
    payload = json.loads(payload)
    if user_id is not None:
        payload["user_id"] = str(user_id)
    payload = json.dumps(payload, separators=(",", ":"))
    payload = base64.urlsafe_b64encode(payload.encode()).decode()
    token[1] = payload.rstrip("=")
    token = ".".join(token)
    return token


class UserRegistrationTest(APITestCase):
    def setUp(self):
        self.url = reverse("user-register")
        self.data = {"email": "testuser@mail.com", "username": "testuser1234", "password": "R286rn5fAWsf"}

    def test_register_account_proper(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=self.data["email"])
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertNotIn("password", response.data)
        self.assertTrue(user.check_password(self.data["password"]))

    def test_register_account_email_exists(self):
        self.client.post(self.url, self.data, format="json")
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertIn("email", response.data)

    def test_register_account_no_email(self):
        data_incomplete = {"username": "testuser1234", "password": "R286rn5fAWsf"}
        response = self.client.post(self.url, data_incomplete, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("email", response.data)

    def test_register_account_no_password(self):
        data_incomplete = {"email": "testuser@mail.com", "username": "testuser1234"}
        response = self.client.post(self.url, data_incomplete, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("password", response.data)

    def test_register_account_no_username(self):
        data_incomplete = {"email": "testuser@mail.com", "password": "R286rn5fAWsf"}
        response = self.client.post(self.url, data_incomplete, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("username", response.data)

    def test_register_account_weak_password(self):
        data_weak_password = {"email": "testuser@mail.com", "username": "testuser1234", "password": "1234"}
        response = self.client.post(self.url, data_weak_password, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn("password", response.data)

    def test_register_disallow_get_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class UserLoginTest(APITestCase):
    def setUp(self):
        self.login_url = reverse("auth-login")
        self.refresh_url = reverse("auth-refresh")
        self.data = {"email": "testuser@mail.com", "username": "testuser1234", "password": "R286rn5fAWsf"}
        self.user = get_user_model().objects.create_user(
            email=self.data["email"], username=self.data["username"], password=self.data["password"]
        )

    def test_login_proper(self):
        response = self.client.post(
            self.login_url, {"email": self.data["email"], "password": self.data["password"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(self.user.id, int(AccessToken(response.data["access"])["user_id"]))

    def test_login_non_existent_user(self):
        response = self.client.post(
            self.login_url, {"email": "nonexistentuser@mail.com", "password": self.data["password"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_no_email(self):
        response = self.client.post(self.login_url, {"password": self.data["password"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertIn("email", response.data)

    def test_login_no_password(self):
        response = self.client.post(self.login_url, {"email": self.data["email"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertIn("password", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url, {"email": self.data["email"], "password": "WrongPassword"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_refresh_token_proper(self):
        response = self.client.post(self.refresh_url, {"refresh": str(RefreshToken.for_user(self.user))}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(self.user.id, int(AccessToken(response.data["access"])["user_id"]))

    def test_refresh_token_forged(self):
        malicious_user = get_user_model().objects.create_user(
            email="muser@mail.com", username="muser", password="R286rn5fAWsf1"
        )
        forged_token = forge_token(str(RefreshToken.for_user(self.user)), malicious_user.id)
        response = self.client.post(self.refresh_url, {"refresh": forged_token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_refresh_token_forged_control(self):
        token = str(RefreshToken.for_user(self.user))
        token = forge_token(token)
        response = self.client.post(self.refresh_url, {"refresh": token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(self.user.id, int(AccessToken(response.data["access"])["user_id"]))
