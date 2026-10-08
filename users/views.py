from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from users.serializers import UserGetMeSerializer, UserRegistrationSerializer


class RegisterView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


class UsersMeView(RetrieveAPIView):
    serializer_class = UserGetMeSerializer

    def get_object(self):
        return self.request.user
