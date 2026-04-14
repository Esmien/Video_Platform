import logging
import sqlparse
from loguru import logger
from pygments import highlight
from pygments.lexers import SqlLexer
from pygments.formatters import TerminalTrueColorFormatter
from sqlparse.exceptions import SQLParseError


class SQLFormatterHandler(logging.Handler):
    """ Обработчик логов SQL на базе loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        """ Обрабатывает сообщение лога (перехватывает, форматирует, выводит)

            Args:
                record - объект записи лога
        """

        # делаем красоту, если работаем с SQL логом
        if hasattr(record, 'sql'):
            raw_sql = record.sql

            if len(raw_sql) > 5000:
                formatted_sql = f'{raw_sql[:500]}\n\n... [Слишком большой запрос: {len(raw_sql)} символов. Скрыто ...'
            else:
                try:
                    # форматируем отступы
                    formatted_sql = sqlparse.format(record.sql, reindent=True, keyword_case='upper')
                except SQLParseError:
                    # если парсер все равно не справился, просто отдаем сырой SQL
                    formatted_sql = raw_sql

            # КРАСИМ СИНТАКСИС для консоли
            colored_sql = highlight(formatted_sql, SqlLexer(), TerminalTrueColorFormatter(style='monokai'))

            # забираем время выполнения из record.duration
            duration = getattr(record, 'duration', 0.0)

            # Убираем лишний перенос строки от pygments (он добавляет свой в конце)
            logger.debug(f"⏱️ [{duration:.3f}s]\n{colored_sql.strip()}")
        else:
            # если лог не SQL, то просто возвращаем его без обработки
            logger.debug(record.getMessage())