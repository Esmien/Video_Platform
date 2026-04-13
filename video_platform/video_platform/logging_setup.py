import logging
import sqlparse
from loguru import logger
from pygments import highlight
from pygments.lexers import SqlLexer
from pygments.formatters import TerminalTrueColorFormatter

class SQLFormatterHandler(logging.Handler):
    def emit(self, record):
        if hasattr(record, 'sql'):
            # Форматируем отступы
            formatted_sql = sqlparse.format(record.sql, reindent=True, keyword_case='upper')

            # КРАСИМ СИНТАКСИС для консоли
            colored_sql = highlight(formatted_sql, SqlLexer(), TerminalTrueColorFormatter(style='monokai'))

            duration = getattr(record, 'duration', 0.0)
            # Убираем лишний перенос строки от pygments (он добавляет свой в конце)
            logger.debug(f"⏱️ [{duration:.3f}s]\n{colored_sql.strip()}")
        else:
            logger.debug(record.getMessage())