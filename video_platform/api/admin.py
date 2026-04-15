from django.contrib import admin

from .models import Video, VideoFile, Like


class VideoFileInline(admin.TabularInline):
    model = VideoFile
    can_delete = True  # Разрешаем удалять файл прямо со страницы видео
    verbose_name_plural = 'Файлы видео'
    extra = 1


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'is_published', 'total_likes', 'created_at', 'get_file_ids', 'get_file_links')
    list_filter = ('is_published', 'created_at')
    search_fields = ('name', 'owner__username')
    readonly_fields = ('total_likes', 'created_at')

    autocomplete_fields = ('owner',)

    inlines = [VideoFileInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner').prefetch_related('files')

    @admin.display(description='ID файлов')
    def get_file_ids(self, obj):
        # Собираем ID всех связанных файлов через генератор
        files = obj.files.all()
        if not files:
            return None
        return ", ".join(str(f.id) for f in files)

    @admin.display(description='Файлы')
    def get_file_links(self, obj):
        # Собираем пути всех файлов
        files = obj.files.all()
        if not files:
            return "Нет файлов"

        return ", ".join(f.quality for f in files if f.file)


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'quality', 'file')
    list_filter = ('quality',)
    search_fields = ('video__name',)
    autocomplete_fields = ('video',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'video', 'user')
    search_fields = ('video__name', 'user__username')

    autocomplete_fields = ('video', 'user')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('video', 'user')