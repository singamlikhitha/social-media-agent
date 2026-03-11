from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.utils.logger import logger


class SchedulerService:
    def __init__(self):
        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.DATABASE_URL),
        }
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone=settings.TIMEZONE,
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")

    def schedule_post(self, post_id: int, run_time: datetime):
        from app.services.posting_service import execute_post_job

        self.scheduler.add_job(
            execute_post_job,
            trigger=DateTrigger(run_date=run_time),
            id=f"post_{post_id}",
            args=[post_id],
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.info(f"Scheduled post {post_id} for {run_time}")

    def reschedule_post(self, post_id: int, new_time: datetime):
        job_id = f"post_{post_id}"
        try:
            self.scheduler.reschedule_job(
                job_id, trigger=DateTrigger(run_date=new_time)
            )
            logger.info(f"Rescheduled post {post_id} to {new_time}")
        except Exception:
            self.schedule_post(post_id, new_time)

    def cancel_post(self, post_id: int):
        job_id = f"post_{post_id}"
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled scheduled post {post_id}")
        except Exception:
            logger.warning(f"No scheduled job found for post {post_id}")

    def add_recurring_analytics_sync(self, interval_hours: int = 6):
        from app.services.posting_service import sync_analytics_job

        self.scheduler.add_job(
            sync_analytics_job,
            trigger=IntervalTrigger(hours=interval_hours),
            id="analytics_sync",
            replace_existing=True,
        )
        logger.info(f"Recurring analytics sync set to every {interval_hours}h")

    def get_pending_jobs(self) -> list[dict]:
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in jobs
        ]


scheduler_service = SchedulerService()
