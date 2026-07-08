from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.utils.logger import logger


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone=settings.TIMEZONE,
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

            # Re-schedule all pending posts from DB and catch missed ones
            self._restore_scheduled_posts()

            # Add periodic job to catch missed posts every 60 seconds
            self.scheduler.add_job(
                self._check_missed_posts,
                trigger=IntervalTrigger(seconds=60),
                id="missed_post_checker",
                replace_existing=True,
            )
            logger.info("Missed-post checker started (every 60s)")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")

    def _restore_scheduled_posts(self):
        """On startup, re-schedule all posts that are still in SCHEDULED status."""
        try:
            from app.database import SessionLocal
            from app.models.post import ScheduledPost, PostStatus

            db = SessionLocal()
            try:
                pending = (
                    db.query(ScheduledPost)
                    .filter(ScheduledPost.status == PostStatus.SCHEDULED)
                    .all()
                )
                now = datetime.now(timezone.utc)
                restored = 0
                immediate = 0

                for post in pending:
                    scheduled = post.scheduled_time
                    if scheduled.tzinfo is None:
                        scheduled = scheduled.replace(tzinfo=timezone.utc)

                    if scheduled <= now:
                        # Missed post — publish immediately
                        logger.info(f"Missed post {post.id} (was scheduled for {post.scheduled_time}), publishing now")
                        self.scheduler.add_job(
                            self._dispatch_publish,
                            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
                            id=f"post_{post.id}",
                            args=[post.id],
                            replace_existing=True,
                            misfire_grace_time=3600,
                        )
                        immediate += 1
                    else:
                        # Future post — re-schedule normally
                        self.scheduler.add_job(
                            self._dispatch_publish,
                            trigger=DateTrigger(run_date=scheduled),
                            id=f"post_{post.id}",
                            args=[post.id],
                            replace_existing=True,
                            misfire_grace_time=300,
                        )
                        restored += 1

                logger.info(f"Restored {restored} future posts, {immediate} missed posts queued for immediate publish")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to restore scheduled posts: {e}")

    def _check_missed_posts(self):
        """Periodic check for posts whose scheduled_time has passed but are still SCHEDULED."""
        try:
            from app.database import SessionLocal
            from app.models.post import ScheduledPost, PostStatus

            db = SessionLocal()
            try:
                now = datetime.now(timezone.utc)
                missed = (
                    db.query(ScheduledPost)
                    .filter(
                        ScheduledPost.status == PostStatus.SCHEDULED,
                        ScheduledPost.scheduled_time <= now,
                    )
                    .all()
                )

                for post in missed:
                    job_id = f"post_{post.id}"
                    existing = None
                    try:
                        existing = self.scheduler.get_job(job_id)
                    except Exception:
                        pass

                    if not existing:
                        logger.info(f"Missed post {post.id} detected, dispatching now")
                        self._dispatch_publish(post.id)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Missed post checker error: {e}")

    def schedule_post(self, post_id: int, run_time: datetime):
        if run_time.tzinfo is None:
            run_time = run_time.replace(tzinfo=timezone.utc)

        self.scheduler.add_job(
            self._dispatch_publish,
            trigger=DateTrigger(run_date=run_time),
            id=f"post_{post_id}",
            args=[post_id],
            replace_existing=True,
            misfire_grace_time=300,
        )
        logger.info(f"Scheduled post {post_id} for {run_time}")

    def _dispatch_publish(self, post_id: int):
        """Dispatch to Celery if available, otherwise run directly."""
        try:
            from app.tasks.post_tasks import publish_post
            publish_post.delay(post_id)
            logger.info(f"Dispatched post {post_id} to Celery")
        except Exception:
            logger.info(f"Celery unavailable, executing post {post_id} directly")
            from app.services.posting_service import execute_post_job
            execute_post_job(post_id)

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
