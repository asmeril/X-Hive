import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from config import settings


class StructuredLogger:
    """
    JSON-formatted structured logger for production monitoring.

    Features:
    - JSON output for easy parsing
    - Contextual fields (task_id, user_id, etc.)
    - Automatic timestamp
    - File rotation support
    """

    def __init__(
        self,
        name: str,
        log_file: Optional[Path] = None,
        console_output: bool = True
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name (usually module name)
            log_file: Optional log file path
            console_output: Whether to also log to console
        """

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []

        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(console_handler)

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

    def _build_log_entry(
        self,
        level: str,
        message: str,
        **context
    ) -> Dict[str, Any]:
        """Build structured log entry"""

        return {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **context
        }

    def info(self, message: str, **context):
        """Log info message with context"""
        entry = self._build_log_entry('INFO', message, **context)
        self.logger.info(json.dumps(entry, ensure_ascii=False))

    def warning(self, message: str, **context):
        """Log warning message with context"""
        entry = self._build_log_entry('WARNING', message, **context)
        self.logger.warning(json.dumps(entry, ensure_ascii=False))

    def error(self, message: str, **context):
        """Log error message with context"""
        entry = self._build_log_entry('ERROR', message, **context)
        self.logger.error(json.dumps(entry, ensure_ascii=False))

    def debug(self, message: str, **context):
        """Log debug message with context"""
        entry = self._build_log_entry('DEBUG', message, **context)
        self.logger.debug(json.dumps(entry, ensure_ascii=False))


class JsonFormatter(logging.Formatter):
    """JSON formatter for log records"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


LOG_DIR = Path(settings.DATA_PATH) / "logs"
STRUCTURED_LOGGER = StructuredLogger(
    name="x-hive",
    log_file=LOG_DIR / "structured.log",
    console_output=True
)

task_logger = STRUCTURED_LOGGER
