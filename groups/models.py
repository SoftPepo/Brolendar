import uuid

from django.conf import settings
from django.db.models import (
    CharField,
    DateTimeField,
    ForeignKey,
    Index,
    Model,
    UUIDField,
)
from django.db.models.deletion import CASCADE, RESTRICT
from django.db.models.fields.composite import CompositePrimaryKey


class Group(Model):
    name = CharField(max_length=30)
    owner = ForeignKey(settings.AUTH_USER_MODEL, on_delete=RESTRICT, related_name="owned_groups")
    invite_id = UUIDField(default=uuid.uuid4, unique=True)
    created_at = DateTimeField(auto_now_add=True)


class GroupMember(Model):
    pk = CompositePrimaryKey("group_id", "user_id")
    user = ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="memberships")
    group = ForeignKey(Group, on_delete=CASCADE, related_name="members")
    joined_at = DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [Index(fields=["user"])]
