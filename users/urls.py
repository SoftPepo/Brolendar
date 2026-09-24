from django.urls import path

from users.views import RegisterView

urlpatterns = [
    path("users/", RegisterView.as_view(), name="user-register"),
]
