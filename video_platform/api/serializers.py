from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Video


User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    """ Сериализатор регистрации пользователя """

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'password')

    def create(self, validated_data: dict) -> User:
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('id', 'name', 'created_at', 'owner_id')


class VideoExpandedSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta(VideoSerializer.Meta):
        fields = ('id', 'name', 'created_at', 'owner_id', 'owner')