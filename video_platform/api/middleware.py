import time
import logging
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

class SQLQueryCountMiddleware:
    """
    Middleware для подсчета количества SQL-запросов и времени выполнения.
    Работает только при DEBUG = True.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # работает только в DEBUG-режиме
        if not settings.DEBUG:
            return self.get_response(request)

        # фиксируем начальные показатели
        start_queries = len(connection.queries)
        start_time = time.time()

        # пропускаем запрос дальше к View
        response = self.get_response(request)

        # снимаем итоговые показатели
        end_time = time.time()
        end_queries = len(connection.queries)

        query_count = end_queries - start_queries
        execution_time = end_time - start_time

        # выводим в лог
        logger.info(
            f"[{request.method}] {request.path} | "
            f"SQL Queries: {query_count} | "
            f"Time: {execution_time:.3f}s"
        )

        return response