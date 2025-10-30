"""
Barker v ESHT - Logging Configuration
Structured logging with JSON output and file rotation
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json
from logging.handlers import TimedRotatingFileHandler


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


def setup_logging(
    log_level: str = 'INFO',
    log_dir: Optional[Path] = None,
    console_output: bool = True
) -> None:
    """Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        console_output: Whether to output to console
    """
    # Get base directory
    if log_dir is None:
        base_dir = Path(__file__).parent.parent.parent
        log_dir = base_dir / 'logs'

    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler for all logs (JSON format)
    all_logs_handler = TimedRotatingFileHandler(
        log_dir / 'system.log',
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    all_logs_handler.setLevel(logging.DEBUG)
    all_logs_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(all_logs_handler)

    # Error log handler (JSON format)
    error_handler = TimedRotatingFileHandler(
        log_dir / 'error.log',
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(error_handler)

    # Automation log handler
    automation_handler = TimedRotatingFileHandler(
        log_dir / 'automation.log',
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    automation_handler.setLevel(logging.INFO)
    automation_handler.setFormatter(JsonFormatter())

    # Add to automation logger
    automation_logger = logging.getLogger('automation')
    automation_logger.addHandler(automation_handler)

    logging.info(f"Logging initialized - Level: {log_level}, Dir: {log_dir}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding extra fields to logs"""

    def __init__(self, logger: logging.Logger, **extra_fields):
        self.logger = logger
        self.extra_fields = extra_fields
        self.old_factory = None

    def __enter__(self):
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.extra_fields = self.extra_fields
            return record

        logging.setLogRecordFactory(record_factory)
        self.old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.old_factory:
            logging.setLogRecordFactory(self.old_factory)
