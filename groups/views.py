from django.db import transaction
from rest_framework.generics import CreateAPIView

from groups.models import GroupMember
from groups.serializers import GroupSerializer


class GroupCreateView(CreateAPIView):
    serializer_class = GroupSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        GroupMember.objects.create(group=group, user=self.request.user)
