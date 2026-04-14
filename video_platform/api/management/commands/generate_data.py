import time
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import OuterRef, Subquery, Count
from django.db.models.functions import Coalesce

from api.models import Video, Like

User = get_user_model()

class Command(BaseCommand):
    help = 'Генерация тестовых данных: 10k пользователей, 100k видео, случайные лайки'

    def handle(self, *args, **options):
        start_time = time.time()

        # Оборачиваем всё в единую транзакцию. Если что-то упадет — база откатится до чистого состояния
        with transaction.atomic():
            self.stdout.write(self.style.WARNING('Удаление старых тестовых данных...'))
            Like.objects.all().delete()
            Video.objects.all().delete()
            # Удаляем всех, кроме админов (суперпользователей)
            User.objects.filter(is_superuser=False).delete()

            # --- 1. Генерация пользователей ---
            self.stdout.write(self.style.SUCCESS('Генерация 10 000 пользователей...'))

            # Хеширование пароля — дорогая операция. Делаем один хеш и раздаем всем
            default_password = make_password('1111')
            users_to_create = [User(username=f'user_{i}', password=default_password) for i in range(10_000)]

            # batch_size делит один огромный INSERT на пачки, чтобы не превысить лимиты памяти СУБД
            User.objects.bulk_create(users_to_create, batch_size=2_000)

            # Достаем ID созданных юзеров плоским списком
            user_ids = list(User.objects.filter(is_superuser=False).values_list('id', flat=True))

            # --- 2. Генерация видео ---
            self.stdout.write(self.style.SUCCESS('Генерация 100 000 видео...'))

            videos_to_create = [
                Video(
                    owner_id=random.choice(user_ids),
                    name=f'Тестовое видео {i}',
                    is_published=True, # По ТЗ нужны опубликованные
                    total_likes=0
                )
                for i in range(100_000)
            ]

            Video.objects.bulk_create(videos_to_create, batch_size=5_000)
            video_ids = list(Video.objects.values_list('id', flat=True))

            # --- 3. Генерация лайков ---
            self.stdout.write(self.style.SUCCESS('Распределение лайков...'))

            likes_to_create = []
            # Используем set, чтобы избежать дубликатов (unique_together не пропустит)
            seen_likes = set()

            # Сгенерируем 300 000 лайков для реалистичности
            for _ in range(300_000):
                v_id = random.choice(video_ids)
                u_id = random.choice(user_ids)

                # Защита от дубликатов
                if (v_id, u_id) not in seen_likes:
                    seen_likes.add((v_id, u_id))
                    likes_to_create.append(Like(video_id=v_id, user_id=u_id))

            Like.objects.bulk_create(likes_to_create, batch_size=10_000)

            # --- 4. Синхронизация счетчика total_likes ---
            self.stdout.write(self.style.SUCCESS('Синхронизация счетчиков лайков в таблице Video...'))

            # считаем количество лайков у видео на уровне БД
            likes_sq = Like.objects.filter(
                video=OuterRef('pk')
            ).values('video').annotate(cnt=Count('id')).values('cnt')

            # Делаем массовый UPDATE на уровне БД
            Video.objects.update(total_likes=Coalesce(Subquery(likes_sq), 0))

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS(f'Готово! Данные успешно сгенерированы за {end_time - start_time:.2f} сек.'))