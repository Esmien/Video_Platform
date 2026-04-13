from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL


#------------------------------------------------------------------------------------#
class Video(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    name = models.CharField(max_length=100, null=False, verbose_name='Название')
    is_published = models.BooleanField(default=False, verbose_name='Статус')
    total_likes = models.IntegerField(default=0, verbose_name='Всего лайков')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        indexes = [models.Index(fields=['owner', 'is_published'])]

    def __str__(self):
        return self.name


#------------------------------------------------------------------------------------#
QUALITY_CHOICES = [
    ('HD', 'HD'),
    ('FHD', 'FHD'),
    ('UHD', 'UHD')
]

class VideoFile(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='files', verbose_name='Видео')
    file = models.FileField(upload_to='videos/', verbose_name='Файл')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='HD', verbose_name='Качество')

    def __str__(self):
        return f'{self.video.name} - {self.quality}'


#------------------------------------------------------------------------------------#
class Like(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes', verbose_name='Видео')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes', verbose_name='Пользователь')

    class Meta:
        unique_together = ('video', 'user')

    def __str__(self):
        return f'Лайк от {self.user_id} на видео {self.video_id}'


#------------------------------------------------------------------------------------#