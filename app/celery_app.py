from celery import Celery
from celery.signals import worker_process_init
from app.config import settings

celery_app = Celery(
    "social_media_saas",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "refresh-expiring-tokens": {
            "task": "app.tasks.token_tasks.refresh_expiring_tokens",
            "schedule": 3600.0,  # Every hour
        },
        "sync-analytics": {
            "task": "app.tasks.analytics_tasks.sync_all_analytics",
            "schedule": 21600.0,  # Every 6 hours
        },
        "cleanup-expired-oauth-states": {
            "task": "app.tasks.token_tasks.cleanup_expired_states",
            "schedule": 600.0,  # Every 10 minutes
        },
    },
)


@worker_process_init.connect(weak=False)
def _init_worker_telemetry(*args, **kwargs):
    """Initialise OpenTelemetry inside each Celery worker process.

    Exporters use background threads, so they must be set up after the worker forks
    (in worker_process_init), not at import time in the parent process.
    """
    from app.telemetry import setup_telemetry, instrument_celery

    setup_telemetry()
    instrument_celery()
