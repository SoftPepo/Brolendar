from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import RegisterView, UsersMeView

urlpatterns = [
    path("users/", RegisterView.as_view(), name="user-register"),
    path("users/me/", UsersMeView.as_view(), name="user-get-me"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
]
