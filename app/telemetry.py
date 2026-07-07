"""
OpenTelemetry setup for the Social Media SaaS Platform.

Provides distributed tracing, metrics, and (optionally) log export over OTLP.
Everything is gated behind ``settings.OTEL_ENABLED`` so that local development and
tests run untouched when telemetry is off.

The metric/trace instruments below are created from the OpenTelemetry *API* (not the
SDK). Before ``setup_telemetry()`` runs, the API returns no-op providers, so importing
and using these instruments is always safe — they simply do nothing until a real
provider is installed. This lets service code call e.g. ``telemetry.posts_published.add(...)``
unconditionally without worrying about whether telemetry is configured.
"""
from __future__ import annotations

import logging
from typing import Optional

from opentelemetry import metrics, trace

from app.config import settings

# --------------------------------------------------------------------------------------
# Tracer / Meter handles (safe to use even when telemetry is disabled — no-op providers)
# --------------------------------------------------------------------------------------
tracer = trace.get_tracer("social_media_agent")
meter = metrics.get_meter("social_media_agent")

# --------------------------------------------------------------------------------------
# Business metric instruments
# --------------------------------------------------------------------------------------
# Post publishing
posts_published = meter.create_counter(
    "smm.posts.published",
    unit="1",
    description="Number of social posts published, labelled by platform and outcome.",
)
post_publish_duration = meter.create_histogram(
    "smm.posts.publish.duration",
    unit="ms",
    description="End-to-end time to publish a scheduled post.",
)

# AI content / media generation
content_generated = meter.create_counter(
    "smm.content.generated",
    unit="1",
    description="Number of AI content generations (ideas, captions, repurpose, etc.).",
)
gemini_requests = meter.create_counter(
    "smm.gemini.requests",
    unit="1",
    description="Calls to the Gemini API, labelled by operation and outcome.",
)
gemini_duration = meter.create_histogram(
    "smm.gemini.duration",
    unit="ms",
    description="Latency of Gemini API calls.",
)
media_generated = meter.create_counter(
    "smm.media.generated",
    unit="1",
    description="AI image/video generations, labelled by kind, source, and outcome.",
)

# OAuth token maintenance
token_refreshes = meter.create_counter(
    "smm.oauth.token_refresh",
    unit="1",
    description="OAuth token refresh attempts, labelled by platform and outcome.",
)

logger = logging.getLogger("social_media_agent")

_initialized = False


def _parse_headers(raw: str) -> Optional[dict]:
    """Parse an 'k1=v1,k2=v2' header string into a dict (or None if empty)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    headers = {}
    for pair in raw.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            headers[key.strip()] = value.strip()
    return headers or None


def _build_exporters():
    """Return (span_exporter, metric_exporter, log_exporter) for the configured protocol."""
    protocol = (settings.OTEL_EXPORTER_OTLP_PROTOCOL or "http/protobuf").lower()
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT or None
    headers = _parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS)

    if protocol.startswith("grpc"):
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

        kwargs = {"headers": headers}
        if endpoint:
            kwargs["endpoint"] = endpoint
        return (
            OTLPSpanExporter(**kwargs),
            OTLPMetricExporter(**kwargs),
            OTLPLogExporter(**kwargs),
        )

    # Default: OTLP over HTTP/protobuf. Each signal has its own path suffix.
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

    def _http_kwargs(signal: str):
        kw = {"headers": headers}
        if endpoint:
            kw["endpoint"] = f"{endpoint.rstrip('/')}/v1/{signal}"
        return kw

    return (
        OTLPSpanExporter(**_http_kwargs("traces")),
        OTLPMetricExporter(**_http_kwargs("metrics")),
        OTLPLogExporter(**_http_kwargs("logs")),
    )


def _build_resource():
    from opentelemetry.sdk.resources import Resource

    return Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": "2.0.0",
            "service.namespace": "social-media-saas",
            "deployment.environment": settings.ENVIRONMENT,
        }
    )


def _setup_tracing(resource, span_exporter):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

    provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(TraceIdRatioBased(settings.OTEL_TRACES_SAMPLER_RATIO)),
    )
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)


def _setup_metrics(resource, metric_exporter):
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30_000)
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)


def _setup_logs(resource, log_exporter):
    """Ship stdlib logging records via OTLP, correlated with the active trace."""
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry._logs import set_logger_provider

    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(provider)

    handler = LoggingHandler(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        logger_provider=provider,
    )
    # Attach to the app logger so its records are exported without duplicating stdout.
    logging.getLogger("social_media_agent").addHandler(handler)


def setup_telemetry(app=None, engine=None) -> bool:
    """
    Initialise OpenTelemetry tracing, metrics, and log export.

    Idempotent and safe to call from both the web app and Celery worker processes.
    Returns True if telemetry was enabled and configured, False otherwise.

    Args:
        app:    optional FastAPI app to auto-instrument (server spans + HTTP metrics).
        engine: optional SQLAlchemy engine to instrument. Defaults to app.database.engine.
    """
    global _initialized
    if _initialized:
        return settings.OTEL_ENABLED

    if not settings.OTEL_ENABLED:
        _initialized = True
        logger.info("Telemetry disabled (OTEL_ENABLED=false); skipping OpenTelemetry setup.")
        return False

    try:
        resource = _build_resource()
        span_exporter, metric_exporter, log_exporter = _build_exporters()

        _setup_tracing(resource, span_exporter)
        _setup_metrics(resource, metric_exporter)
        if settings.OTEL_EXPORT_LOGS:
            _setup_logs(resource, log_exporter)

        _instrument_libraries(app=app, engine=engine)

        _initialized = True
        logger.info(
            "OpenTelemetry initialised (service=%s, env=%s, protocol=%s, endpoint=%s)",
            settings.OTEL_SERVICE_NAME,
            settings.ENVIRONMENT,
            settings.OTEL_EXPORTER_OTLP_PROTOCOL,
            settings.OTEL_EXPORTER_OTLP_ENDPOINT or "<sdk-default>",
        )
        return True
    except Exception as exc:  # never let telemetry break the app
        logger.error("Failed to initialise OpenTelemetry: %s", exc, exc_info=True)
        _initialized = True
        return False


def _instrument_libraries(app=None, engine=None):
    """Auto-instrument FastAPI, SQLAlchemy, HTTPX, and Redis. Each guarded independently."""
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(
                app,
                excluded_urls="/api/health,/api/health/.*",
            )
        except Exception as exc:
            logger.warning("FastAPI instrumentation failed: %s", exc)

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        if engine is None:
            from app.database import engine as db_engine

            engine = db_engine
        SQLAlchemyInstrumentor().instrument(engine=engine)
    except Exception as exc:
        logger.warning("SQLAlchemy instrumentation failed: %s", exc)

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception as exc:
        logger.warning("HTTPX instrumentation failed: %s", exc)

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except Exception as exc:
        logger.warning("Redis instrumentation failed: %s", exc)


def instrument_celery():
    """Instrument Celery task execution. Call once from a worker_process_init signal."""
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        CeleryInstrumentor().instrument()
        logger.info("Celery instrumentation enabled.")
    except Exception as exc:
        logger.warning("Celery instrumentation failed: %s", exc)
