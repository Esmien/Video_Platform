from enum import StrEnum
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, extend_schema_view
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from django.db.models import Q

from .exceptions import *
from .mixins import PaginatedResponseMixin
from .models import Video
from .serializers import VideoSerializer, VideoExpandedSerializer, RegisterSerializer
from .permissions import IsPublishedOrOwner
from .services import LikeService, VideoService

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """ Представление регистрации пользователя """

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

@extend_schema_view(
    list=extend_schema(
        summary="Список видео",
        description="""
        Получение списка видео.
        Отдает записи из БД со всеми доступными видео.
        Неавторизованные пользователи видят только опубликованные ролики.
        """
    ),
    retrieve=extend_schema(
        summary="Детали о видео",
        description="""
        Получение конкретного видео.
        Отдает конкретную запись по ID.
        При статусе `is_published=False` видео видно только его владельцу.
        """
    )
)
class VideoViewSet(PaginatedResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с видео-платформой.

    Endpoints:
        * (GET) /v1/videos/ - Отдает записи из БД со всеми видео
        * (GET) /v1/videos/{id}/ - Отдает конкретную запись по ID (при статусе is_published=False видео видны только owner'у)
        * (POST) /v1/videos/{id}/likes/ - Ставит лайк от пользователя на выбранное видео, требуется авторизация
        * (GET) /v1/videos/ids/ - Отдает список ID всех опубликованных видео
        * (GET) /v1/videos/statistics-group-by/ - Отдает статистику по всем видео в формате video_id: total_likes при помощи GROUP BY
        * (GET) /v1/videos/statistics-subquery/ - Отдает статистику по всем видео в формате video_id: total_likes при помощи подзапроса
    """

    class Messages(StrEnum):
        DOES_NOT_EXIST = 'Видео не найдено'
        SELF_LIKE = 'Нельзя поставить лайк самому себе'
        DUPLICATE = 'Вы уже ставили лайк'
        SUCCESS = 'Лайк поставлен'

    permission_classes = (IsAuthenticatedOrReadOnly, IsPublishedOrOwner)

    def get_queryset(self):
        # делаем inner join с User, подтягивая таблицу с пользователями
        qs = Video.objects.select_related('owner').all()

        # отдаем список опубликованных видео либо список видео автора
        if self.action == 'list':
            if self.request.user.is_authenticated:
                qs = qs.filter(Q(is_published=True) | Q(owner=self.request.user))
            else:
                qs = qs.filter(is_published=True)

        return qs

    def get_serializer_class(self):
        # Обрабатываем параметр ?user_expand=true для детального просмотра
        if self.action == 'retrieve':
            expand = self.request.query_params.get('user_expand', '').lower() == 'true'
            if expand:
                return VideoExpandedSerializer

        return VideoSerializer


    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def likes(self, request: Request, pk: int | None=None) -> Response:
        """
        **`POST` /v1/videos/{id}/likes/**
          Ставит лайк от пользователя на выбранное видео. **Требуется авторизация**.
          """

        user_id = request.user.pk
        video_id = pk
        try:
            LikeService.put_like(user_id=user_id, video_id=video_id)
        except VideoNotFoundError:
            return Response({'detail': self.Messages.DOES_NOT_EXIST}, status.HTTP_404_NOT_FOUND)
        except SelfLikeError:
            return Response({'detail': self.Messages.SELF_LIKE}, status.HTTP_400_BAD_REQUEST)
        except DuplicateLikeError:
            return Response({'detail': self.Messages.DUPLICATE}, status.HTTP_400_BAD_REQUEST)

        return Response({'detail': self.Messages.SUCCESS}, status.HTTP_201_CREATED)

    @extend_schema(parameters=[
        OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Номер страницы для пагинации')])
    @action(detail=False, methods=['get'])
    def ids(self, request: Request) -> Response:
        """
         **`GET` /v1/videos/ids/**
          Отдает плоский список ID всех опубликованных видео.
          """

        video_ids = VideoService.get_video_ids()

        return self._get_paginated_response(video_ids)

    @extend_schema(parameters=[
        OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Номер страницы для пагинации')])
    @action(detail=False, methods=['get'], url_path='statistics-subquery')
    def statistics_subquery(self, request: Request) -> Response:
        """
         **`GET` /v1/videos/statistics-subquery/**
          Отдает статистику по всем видео в формате `video_id: total_likes` при помощи подзапроса `Subquery`.
          """

        qs = VideoService.get_statistics_subquery()

        return self._get_paginated_response(qs)

    @extend_schema(parameters=[
        OpenApiParameter(name='page', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description='Номер страницы для пагинации')])
    @action(detail=False, methods=['get'], url_path='statistics-group-by')
    def statistics_group_by(self, request: Request) -> Response:
        """
         **`GET` /v1/videos/statistics-group-by/**
          Отдает статистику по всем видео в формате `video_id: total_likes` при помощи агрегации `GROUP BY`.
          """
        # values() перед annotate(), чтобы ОРМ сделала группировку по указанным полям и left join для видео-лайки
        qs = VideoService.get_statistics_group_by()

        return self._get_paginated_response(qs)