from rest_framework import viewsets

from .models import Video
from .serializers import VideoSerializer


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    # делаем inner join, подтягивая таблицу с пользователями
    queryset = Video.objects.select_related('owner').all()
    serializer_class = VideoSerializer


