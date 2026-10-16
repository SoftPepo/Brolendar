from rest_framework.serializers import ModelSerializer

from groups.models import Group


class GroupSerializer(ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name", "owner", "invite_id", "created_at"]
        read_only_fields = ["id", "owner", "invite_id", "created_at"]
