from enum import StrEnum
from django.db import transaction
from django.db.models import F, QuerySet, OuterRef, Count, Subquery
from django.db.models.functions import Coalesce
from rest_framework import status

from .models import Video, Like


class LikeService:
    """ Бизнес-логика работы с лайками """
    class Messages(StrEnum):
        DOES_NOT_EXIST = 'Видео не найдено'
        SELF_LIKE = 'Нельзя поставить лайк самому себе'
        DUPLICATE = 'Вы уже ставили лайк'
        SUCCESS = 'Лайк поставлен'

    @classmethod
    def put_like(cls, user_id: int, video_id: int) -> tuple[dict[str, Messages], int]:
        """
        Ставит лайк на выбранное видео с проверкой прав на это действие

        Args:
            user_id: id пользователя, ставящего лайк
            video_id: id лайкаемого видео

        Returns:
            Результат операции, статус-код (201, 400, 404)
        """
        # проверяем на наличие видео в БД
        try:
            locked_video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            return {'detail': cls.Messages.DOES_NOT_EXIST}, status.HTTP_404_NOT_FOUND

        # прячем неопубликованные видео от всех, кроме владельца
        if not locked_video.is_published and locked_video.owner_id != user_id:
            return {'detail': cls.Messages.DOES_NOT_EXIST}, status.HTTP_404_NOT_FOUND

        # запрещаем поставить лайк самому себе
        if locked_video.owner_id == user_id:
            return {'detail': cls.Messages.SELF_LIKE}, status.HTTP_400_BAD_REQUEST

        # transaction.atomic() и select_for_update() спасают от race condition, образовывая очередь из запросов,
        # если два юзера одновременно лайкнут видео, total_likes обновится корректно
        with transaction.atomic():
            locked_video = Video.objects.select_for_update().get(pk=video_id)

            # проверка на дубликат лайка, если он уже есть, created будет False
            like, created = Like.objects.get_or_create(video=locked_video, user_id=user_id)
            if not created:
                return {'detail': cls.Messages.DUPLICATE}, status.HTTP_400_BAD_REQUEST

            # безопасно увеличиваем счетчик лайков на стороне бд
            locked_video.total_likes = F('total_likes') + 1
            locked_video.save(update_fields=['total_likes'])

        return {'detail': cls.Messages.SUCCESS}, status.HTTP_201_CREATED

class VideoService:
    """ Бизнес-логика работы с видео """
    @staticmethod
    def get_video_ids() -> QuerySet:
        """ Отдает Queryset для получения списка ID всех видео """

        return Video.objects.filter(is_published=True).order_by('id').values_list('id', flat=True)

    @staticmethod
    def get_statistics_subquery() -> QuerySet:
        """ Отдает Queryset для получения статистики способом подзапроса """

        # Подзапрос: считаем лайки для основного запроса
        likes_sq = Like.objects.filter(
            video=OuterRef('pk')
        ).values('video').annotate(cnt=Count('id')).values('cnt')

        # Основной запрос: аннотируем результат подзапроса
        qs = Video.objects.annotate(
            total_likes=Coalesce(Subquery(likes_sq), 0)
        ).values('id', 'total_likes').order_by('id')

        return qs

    @staticmethod
    def get_statistics_group_by() -> QuerySet:
        """ Отдает Queryset для получения статистики способом GROUP BY """
        # values() перед annotate(), чтобы ОРМ сделала группировку по указанным полям и left join для видео-лайки
        qs = Video.objects.values('id').annotate(
            total_likes=Count('likes')
        ).order_by('id')

        return qs