from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from groups.models import Group, GroupMember
from groups.permissions import IsGroupOwnerOrReadOnly
from groups.serializers import GroupSerializer


class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated, IsGroupOwnerOrReadOnly)

    def get_queryset(self):
        return Group.objects.filter(members__user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        GroupMember.objects.create(group=group, user=self.request.user)
