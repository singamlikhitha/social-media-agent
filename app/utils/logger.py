import json
import logging
import sys
from app.config import settings

try:
    from opentelemetry import trace as _otel_trace
except Exception:  # opentelemetry not installed / import error — degrade gracefully
    _otel_trace = None


class TraceContextFilter(logging.Filter):
    """Inject the active OpenTelemetry trace/span IDs onto every LogRecord.

    Enables correlating log lines with distributed traces. When there is no active
    recording span (or OTel is unavailable) the fields are empty strings.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        trace_id = span_id = ""
        if _otel_trace is not None:
            span = _otel_trace.get_current_span()
            ctx = span.get_span_context() if span else None
            if ctx is not None and getattr(ctx, "is_valid", False):
                trace_id = format(ctx.trace_id, "032x")
                span_id = format(ctx.span_id, "016x")
        record.otel_trace_id = trace_id
        record.otel_span_id = span_id
        return True


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log line — suitable for Cloud Logging / OTLP backends."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            # `severity` is the field Google Cloud Logging reads for log level.
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "location": f"{record.module}:{record.funcName}:{record.lineno}",
        }
        trace_id = getattr(record, "otel_trace_id", "")
        span_id = getattr(record, "otel_span_id", "")
        if trace_id:
            payload["trace_id"] = trace_id
            payload["span_id"] = span_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable formatter that appends the trace id when present."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        trace_id = getattr(record, "otel_trace_id", "")
        if trace_id:
            base = f"{base} | trace_id={trace_id}"
        return base


def setup_logger(name: str = "social_media_agent") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(TraceContextFilter())

        if settings.LOG_FORMAT.lower() == "json":
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                TextFormatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
        logger.addHandler(handler)

    return logger


logger = setup_logger()
