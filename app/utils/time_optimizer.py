from collections import defaultdict
from datetime import datetime


def calculate_optimal_times(
    engagement_data: list[dict],
    top_n: int = 5,
) -> list[dict]:
    """Calculate optimal posting times from historical engagement data.

    Args:
        engagement_data: list of dicts with 'posted_at' (datetime) and 'engagement_rate' (float)
        top_n: number of top slots to return

    Returns:
        List of optimal time slots sorted by engagement.
    """
    if not engagement_data:
        return _default_times()

    slots: dict[tuple[int, int], list[float]] = defaultdict(list)
    now = datetime.utcnow()

    for entry in engagement_data:
        posted_at = entry["posted_at"]
        engagement = entry["engagement_rate"]

        day = posted_at.weekday()
        hour = posted_at.hour
        key = (day, hour)

        days_ago = (now - posted_at).days
        recency_weight = max(0.1, 1.0 - (days_ago / 365))
        slots[key].append(engagement * recency_weight)

    results = []
    for (day, hour), values in slots.items():
        avg = sum(values) / len(values)
        results.append(
            {
                "day_of_week": day,
                "hour": hour,
                "avg_engagement": round(avg, 4),
                "sample_size": len(values),
            }
        )

    results.sort(key=lambda x: x["avg_engagement"], reverse=True)
    return results[:top_n]


def _default_times() -> list[dict]:
    """Return general best-practice posting times when no data is available."""
    defaults = [
        (1, 11),  # Tuesday 11am
        (2, 10),  # Wednesday 10am
        (3, 14),  # Thursday 2pm
        (4, 10),  # Friday 10am
        (0, 11),  # Monday 11am
    ]
    return [
        {
            "day_of_week": day,
            "hour": hour,
            "avg_engagement": 0.0,
            "sample_size": 0,
        }
        for day, hour in defaults
    ]
