from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from groups.models import Group, GroupMember


def create_user(email: str):
    return get_user_model().objects.create_user(email=email, username=email.split("@")[0], password="R286rn5fAWsf")


def create_group(owner, name: str, members=()) -> Group:
    group = Group.objects.create(name=name, owner=owner)
    GroupMember.objects.create(group=group, user=owner)
    for member in members:
        GroupMember.objects.create(group=group, user=member)
    return group


class GroupCreationTest(APITestCase):
    def setUp(self):
        self.create_url = reverse("group-list")
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


class GroupListTest(APITestCase):
    def setUp(self):
        self.list_url = reverse("group-list")
        self.user = create_user("user@test.com")
        self.other_user = create_user("other@test.com")
        self.own_group = create_group(self.user, "OwnGroup")
        self.other_group = create_group(self.other_user, "OtherGroup")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.user)}")

    def test_list_groups_only_own(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.own_group.id)

    def test_list_groups_includes_groups_where_member_not_owner(self):
        create_group(self.other_user, "SharedGroup", members=[self.user])
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class GroupDetailTest(APITestCase):
    def setUp(self):
        self.owner = create_user("owner@test.com")
        self.member = create_user("member@test.com")
        self.outsider = create_user("outsider@test.com")
        self.group = create_group(self.owner, "TestGroup", members=[self.member])
        self.detail_url = reverse("group-detail", args=[self.group.pk])

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_retrieve_group_proper(self):
        self.authenticate(self.member)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.group.id)
        self.assertEqual(response.data["name"], "TestGroup")

    def test_retrieve_group_not_a_member(self):
        self.authenticate(self.outsider)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_group_proper(self):
        self.authenticate(self.owner)
        response = self.client.patch(self.detail_url, {"name": "NewName"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "NewName")

    def test_update_group_not_owner(self):
        self.authenticate(self.member)
        response = self.client.patch(self.detail_url, {"name": "NewName"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "TestGroup")

    def test_update_group_not_a_member(self):
        self.authenticate(self.outsider)
        response = self.client.patch(self.detail_url, {"name": "NewName"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "TestGroup")

    def test_delete_group_proper(self):
        self.authenticate(self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(pk=self.group.pk).exists())
        self.assertFalse(GroupMember.objects.filter(group_id=self.group.pk).exists())

    def test_delete_group_not_owner(self):
        self.authenticate(self.member)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Group.objects.filter(pk=self.group.pk).exists())
