from django.db.models import QuerySet
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .paginators import VideoCursorPagination


class PaginatedResponseMixin:
    def _get_paginated_response(self: GenericAPIView, queryset: QuerySet, is_serializer: bool = False) -> Response:
        """Вспомогательный метод для пагинации кастомных QuerySet"""

        page = self.paginate_queryset(queryset)

        # определяем источник данных (кусок для страницы или весь QuerySet)
        source = page if page is not None else queryset

        # трансформируем данные (прогоняем через сериализатор, если нужно)
        data = self.get_serializer(source, many=True).data if is_serializer else source

        # отдаем правильный объект Response
        if page is not None:
            return self.get_paginated_response(data).data

        # если пагинации нет, отдаем сырые данные
        return data if is_serializer else list(data)


class CursorPaginationMixin:
    pagination_class = VideoCursorPagination