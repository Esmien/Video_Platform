from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL


#------------------------------------------------------------------------------------#
class Video(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    name = models.CharField(max_length=100, null=False)
    is_published = models.BooleanField(default=False)
    total_likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

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
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='videos/')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, default='HD')

    def __str__(self):
        return f'{self.video.name} - {self.quality}'


#------------------------------------------------------------------------------------#
class Like(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('video', 'user')

    def __str__(self):
        return f'Лайк от {self.user_id} на видео {self.video_id}'


#------------------------------------------------------------------------------------#