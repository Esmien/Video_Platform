from django.db import transaction
from django.db.models import F, QuerySet, OuterRef, Count, Subquery
from django.db.models.functions import Coalesce

from .models import Video, Like
from .exceptions import VideoNotFoundError, SelfLikeError, DuplicateLikeError

class LikeService:
    """ Бизнес-логика работы с лайками """

    @classmethod
    def put_like(cls, user_id: int, video_id: int) -> None:
        """
        Ставит лайк на выбранное видео с проверкой прав на это действие

        Args:
            user_id - id пользователя, ставящего лайк
            video_id - id лайкаемого видео

        Raises:
            VideoNotFound - при обращении к несуществующему ID видео
            SelfLikeError - при постановке лайк самому себе
            DuplicateError - при постановке лайка на одно и то же видео, если ранее он был поставлен
        """

        # проверяем на наличие видео в БД
        try:
            locked_video = Video.objects.get(pk=video_id)
        except Video.DoesNotExist:
            raise VideoNotFoundError

        # прячем неопубликованные видео от всех, кроме владельца
        if not locked_video.is_published and locked_video.owner_id != user_id:
            raise VideoNotFoundError

        # запрещаем поставить лайк самому себе
        if locked_video.owner_id == user_id:
            raise SelfLikeError

        # transaction.atomic() и select_for_update() спасают от race condition, образовывая очередь из запросов,
        # если два юзера одновременно лайкнут видео, total_likes обновится корректно
        with transaction.atomic():
            # осознанно дублируем первый запрос для сокращения времени выполнения транзакции
            locked_video = Video.objects.select_for_update().get(pk=video_id)

            # проверка на дубликат лайка, если он уже есть, created будет False
            like, created = Like.objects.get_or_create(video=locked_video, user_id=user_id)
            if not created:
                raise DuplicateLikeError

            # безопасно увеличиваем счетчик лайков на стороне бд
            locked_video.total_likes = F('total_likes') + 1
            locked_video.save(update_fields=['total_likes'])

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
            calculated_likes=Coalesce(Subquery(likes_sq), 0)
        ).values('id', 'calculated_likes').order_by('id')

        return qs

    @staticmethod
    def get_statistics_group_by() -> QuerySet:
        """ Отдает Queryset для получения статистики способом GROUP BY """

        # values() перед annotate(), чтобы ОРМ сделала группировку по указанным полям и left join для видео-лайки
        qs = Video.objects.values('id').annotate(
            calculated_likes=Count('likes')
        ).order_by('id')

        return qs