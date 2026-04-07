from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Video


User = get_user_model()

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