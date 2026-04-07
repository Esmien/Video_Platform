from django.contrib import admin
from .models import Video, VideoFile, Like

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_published', 'total_likes', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('total_likes', 'created_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'quality', 'file')
    list_filter = ('quality',)
    search_fields = ('video__name',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'user')
    search_fields = ('video__name', 'user__username')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video', 'user')