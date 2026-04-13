from django.db.models import QuerySet
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from .paginators import VideoCursorPagination


class PaginatedResponseMixin:
    def _get_paginated_response(self: GenericAPIView, queryset: QuerySet) -> Response:
        """Вспомогательный метод для пагинации кастомных QuerySet"""

        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(page)

        return Response(list(queryset), status=status.HTTP_200_OK)


class CursorPaginationMixin:
    pagination_class = VideoCursorPagination