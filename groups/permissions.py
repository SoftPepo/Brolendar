from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsGroupOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.method in SAFE_METHODS or request.user == obj.owner)
