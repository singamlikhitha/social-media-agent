from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.post import ScheduledPost, PostStatus, Platform
from app.models.analytics import EngagementMetric
from app.services.instagram_service import instagram_service
from app.services.youtube_service import youtube_service
from app.utils.time_optimizer import calculate_optimal_times
from app.utils.logger import logger


class AnalyticsService:
    async def sync_post_analytics(self, post_id: int, db: Session) -> dict:
        post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
        if not post or not post.platform_post_id:
            raise ValueError(f"Post {post_id} not found or not published")

        metrics = {}
        if post.platform == Platform.INSTAGRAM:
            metrics = await instagram_service.get_media_insights(post.platform_post_id)
        elif post.platform == Platform.YOUTUBE:
            metrics = youtube_service.get_video_statistics(post.platform_post_id)

        for name, value in metrics.items():
            metric = EngagementMetric(
                post_id=post_id,
                platform=post.platform.value,
                metric_name=name,
                metric_value=float(value),
            )
            db.add(metric)

        db.commit()
        logger.info(f"Synced analytics for post {post_id}: {len(metrics)} metrics")
        return metrics

    async def sync_all_recent_posts(self, db: Session) -> int:
        cutoff = datetime.utcnow() - timedelta(days=30)
        posts = (
            db.query(ScheduledPost)
            .filter(
                ScheduledPost.status == PostStatus.PUBLISHED,
                ScheduledPost.scheduled_time >= cutoff,
                ScheduledPost.platform_post_id.isnot(None),
            )
            .all()
        )

        synced = 0
        for post in posts:
            try:
                await self.sync_post_analytics(post.id, db)
                synced += 1
            except Exception as e:
                logger.error(f"Failed to sync analytics for post {post.id}: {e}")

        return synced

    def get_post_analytics(self, post_id: int, db: Session) -> list[EngagementMetric]:
        return (
            db.query(EngagementMetric)
            .filter(EngagementMetric.post_id == post_id)
            .order_by(EngagementMetric.recorded_at.desc())
            .all()
        )

    def get_platform_overview(
        self, platform: str, days: int, db: Session
    ) -> dict:
        cutoff = datetime.utcnow() - timedelta(days=days)

        total_posts = (
            db.query(ScheduledPost)
            .filter(
                ScheduledPost.platform == platform,
                ScheduledPost.status == PostStatus.PUBLISHED,
                ScheduledPost.scheduled_time >= cutoff,
            )
            .count()
        )

        def _sum_metric(name: str) -> float:
            result = (
                db.query(func.sum(EngagementMetric.metric_value))
                .filter(
                    EngagementMetric.platform == platform,
                    EngagementMetric.metric_name == name,
                    EngagementMetric.recorded_at >= cutoff,
                )
                .scalar()
            )
            return float(result or 0)

        impressions = _sum_metric("impressions")
        reach = _sum_metric("reach")
        likes = _sum_metric("likes")
        comments = _sum_metric("comments")

        total_engagement = likes + comments
        avg_engagement_rate = (
            (total_engagement / impressions * 100) if impressions > 0 else 0.0
        )

        return {
            "platform": platform,
            "total_posts": total_posts,
            "total_impressions": impressions,
            "total_reach": reach,
            "total_likes": likes,
            "total_comments": comments,
            "avg_engagement_rate": round(avg_engagement_rate, 2),
            "period_days": days,
        }

    def get_optimal_times(self, platform: str, db: Session) -> list[dict]:
        metrics = (
            db.query(
                ScheduledPost.scheduled_time,
                func.sum(EngagementMetric.metric_value).label("total_engagement"),
            )
            .join(EngagementMetric, EngagementMetric.post_id == ScheduledPost.id)
            .filter(
                ScheduledPost.platform == platform,
                ScheduledPost.status == PostStatus.PUBLISHED,
                EngagementMetric.metric_name.in_(["likes", "comments", "shares", "saves"]),
            )
            .group_by(ScheduledPost.id)
            .all()
        )

        engagement_data = [
            {
                "posted_at": row.scheduled_time,
                "engagement_rate": float(row.total_engagement),
            }
            for row in metrics
        ]

        return calculate_optimal_times(engagement_data)

    def get_top_posts(
        self, platform: str, db: Session, limit: int = 10
    ) -> list[dict]:
        results = (
            db.query(
                ScheduledPost.id,
                ScheduledPost.content_text,
                ScheduledPost.platform,
                ScheduledPost.scheduled_time,
                func.sum(EngagementMetric.metric_value).label("total_engagement"),
            )
            .join(EngagementMetric, EngagementMetric.post_id == ScheduledPost.id)
            .filter(
                ScheduledPost.platform == platform,
                EngagementMetric.metric_name.in_(["likes", "comments", "shares", "saves", "views"]),
            )
            .group_by(ScheduledPost.id)
            .order_by(func.sum(EngagementMetric.metric_value).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "post_id": row.id,
                "content_text": row.content_text,
                "platform": row.platform,
                "total_engagement": float(row.total_engagement),
                "published_at": row.scheduled_time,
            }
            for row in results
        ]


analytics_service = AnalyticsService()
