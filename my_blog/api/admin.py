from django.contrib import admin

from .models import Video, VideoFile, Like
# Register your models here.
admin.site.register(Video)
admin.site.register(VideoFile)
admin.site.register(Like)