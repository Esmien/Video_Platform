from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q, Subquery, OuterRef, Count, F
from django.db.models.functions import Coalesce
from django.db import transaction

from .models import Video, Like
from .serializers import VideoSerializer, VideoExpandedSerializer
from .permissions import IsPublishedOrOwner


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsPublishedOrOwner)

    def get_queryset(self):
        # делаем inner join, подтягивая таблицу с пользователями
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
        """ POST /v1/videos/{video.id}/likes/ """

        # get_object() сам проверит IsPublishedOrOwner и выкинет 404/403
        video = self.get_object()
        user = request.user

        msgs = {
            'SELF_LIKE': 'Нельзя поставить лайк самому себе',
            'DUPLICATE': 'Вы уже ставили лайк',
            'SUCCESS': 'Лайк поставлен',
        }

        if video.owner == user:
            return Response(data={'detail': msgs['SELF_LIKE']}, status=status.HTTP_400_BAD_REQUEST)

        # transaction.atomic() и select_for_update() спасают от race condition, образовывая очередь из запросов,
        # если два юзера одновременно лайкнут видео, total_likes обновится корректно
        with transaction.atomic():
            video = Video.objects.select_for_update().get(pk=video.pk)

            # Попытка поставить лайк, если он уже есть, created будет False
            like, created = Like.objects.get_or_create(video=video, user=user)
            if not created:
                return Response(data={'detail': msgs['DUPLICATE']}, status=status.HTTP_400_BAD_REQUEST)

            # безопасно увеличиваем счетчик лайков на стороне бд
            video.total_likes = F('total_likes') + 1
            video.save(update_fields=['total_likes'])

        return Response(data={'detail': msgs['SUCCESS']}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def ids(self, request: Request) -> Response:
        """ GET /v1/videos/ids/ """

        # достаем ID всех опубликованных видео сразу в плоский список
        video_ids = Video.objects.filter(is_published=True).values_list('id', flat=True)

        return Response(list(video_ids), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='statistics-subquery')
    def statistics_subquery(self, request: Request) -> Response:
        """ GET /v1/videos/statistics-subquery/ """

        # Подзапрос: считаем лайки для основного запроса
        likes_sq = Like.objects.filter(
            video=OuterRef('pk')
        ).values('video').annotate(cnt=Count('id')).values('cnt')

        # Основной запрос: аннотируем результат подзапроса
        qs = Video.objects.annotate(
            calculated_likes=Coalesce(Subquery(likes_sq), 0)
        ).values('id', 'calculated_likes')

        results = [{"id": item['id'], "total_likes": item['calculated_likes']} for item in qs]
        return Response(results, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='statistics-group-by')
    def statistics_group_by(self, request):
        """ GET /v1/videos/statistics-group-by/ """
        # values() перед annotate(), чтобы ОРМ сделала группировку по указанным полям
        qs = Video.objects.values('id').annotate(
            calculated_likes=Count('likes')
        )

        results = [{"id": item['id'], "total_likes": item['calculated_likes']} for item in qs]
        return Response(results, status=status.HTTP_200_OK)