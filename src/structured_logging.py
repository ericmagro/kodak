"""Structured JSON logging for production debugging."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }

        # Add extra fields if present
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'message', 'exc_info',
                'exc_text', 'stack_info', 'getMessage'
            }:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def setup_structured_logging(
    level: str = "INFO",
    enable_json: bool = True,
    logger_name: str = "kodak"
) -> logging.Logger:
    """Setup structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Whether to use JSON formatting (False for development)
        logger_name: Name of the logger to configure

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))

    # Set formatter based on mode
    if enable_json:
        formatter = JSONFormatter()
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


def log_user_action(
    logger: logging.Logger,
    action: str,
    user_id: str,
    **kwargs: Any
) -> None:
    """Log a structured user action event.

    Args:
        logger: Logger instance to use
        action: Action being performed
        user_id: User ID performing the action
        **kwargs: Additional context data
    """
    logger.info(
        f"User action: {action}",
        extra={
            "event_type": "user_action",
            "action": action,
            "user_id": user_id,
            **kwargs
        }
    )


def log_session_event(
    logger: logging.Logger,
    event: str,
    session_id: str,
    user_id: str,
    **kwargs: Any
) -> None:
    """Log a structured session event.

    Args:
        logger: Logger instance to use
        event: Type of session event
        session_id: Session ID
        user_id: User ID
        **kwargs: Additional context data
    """
    logger.info(
        f"Session event: {event}",
        extra={
            "event_type": "session_event",
            "event": event,
            "session_id": session_id,
            "user_id": user_id,
            **kwargs
        }
    )


def log_llm_request(
    logger: logging.Logger,
    model: str,
    tokens: Optional[int] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    **kwargs: Any
) -> None:
    """Log a structured LLM request event.

    Args:
        logger: Logger instance to use
        model: Model used
        tokens: Number of tokens (if available)
        duration_ms: Request duration in milliseconds
        success: Whether the request succeeded
        **kwargs: Additional context data
    """
    logger.info(
        f"LLM request to {model}",
        extra={
            "event_type": "llm_request",
            "model": model,
            "tokens": tokens,
            "duration_ms": duration_ms,
            "success": success,
            **kwargs
        }
    )


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any],
    user_id: Optional[str] = None
) -> None:
    """Log an error with structured context.

    Args:
        logger: Logger instance to use
        error: Exception that occurred
        context: Context information about the error
        user_id: User ID if relevant
    """
    extra_data = {
        "event_type": "error",
        "error_type": type(error).__name__,
        "context": context,
    }

    if user_id:
        extra_data["user_id"] = user_id

    logger.error(
        f"Error: {str(error)}",
        extra=extra_data,
        exc_info=True
    )