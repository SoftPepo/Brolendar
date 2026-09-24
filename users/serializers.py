from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer


class UserRegistrationSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "email", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, password):
        try:
            password_validation.validate_password(password)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return password

    def create(self, validated_data):
        model = get_user_model().objects
        return model.create_user(**validated_data)
