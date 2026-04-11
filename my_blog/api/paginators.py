from rest_framework.pagination import CursorPagination


class VideoCursorPagination(CursorPagination):
    page_size = 50
    ordering = 'id'

    def _get_position_from_instance(self, instance, ordering):
        # Если элемент - это просто число (плоский список), само число и есть курсор
        if isinstance(instance, int):
            return str(instance)

        # Для всего остального (объекты моделей, словари) используем стандартную логику DRF
        return super()._get_position_from_instance(instance, ordering)