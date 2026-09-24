from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class AccountTest(APITestCase):

    def setUp(self):
        self.url = reverse('user-register')
        self.data = {'email': 'testuser@mail.com', 'username': 'testuser1234', 'password': 'R286rn5fAWsf'}

    def test_register_account_proper(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=self.data['email'])
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertNotIn('password', response.data)
        self.assertTrue(user.check_password(self.data['password']))

    def test_register_account_email_exists(self):
        self.client.post(self.url, self.data, format='json')
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertIn('email', response.data)

    def test_register_account_no_email(self):
        data_incomplete = {'username': 'testuser1234', 'password': 'R286rn5fAWsf'}
        response = self.client.post(self.url, data_incomplete, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn('email', response.data)

    def test_register_account_no_password(self):
        data_incomplete = {'email': 'testuser@mail.com', 'username': 'testuser1234'}
        response = self.client.post(self.url, data_incomplete, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn('password', response.data)

    def test_register_account_no_username(self):
        data_incomplete = {'email': 'testuser@mail.com', 'password': 'R286rn5fAWsf'}
        response = self.client.post(self.url, data_incomplete, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn('username', response.data)

    def test_register_account_weak_password(self):
        data_weak_password = {'email': 'testuser@mail.com', 'username': 'testuser1234', 'password': '1234'}
        response = self.client.post(self.url, data_weak_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertIn('password', response.data)

    def test_register_disallow_get_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)