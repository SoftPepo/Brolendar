from django.db import transaction
from rest_framework.viewsets import ModelViewSet

from groups.models import GroupMember, Group
from groups.serializers import GroupSerializer


class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(groupmember__user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        GroupMember.objects.create(group=group, user=self.request.user)