"""
CRON task: anonymize suspended users whose scheduled_deletion_at has passed.
Runs nightly at midnight via the lifespan scheduler.
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def anonymize_expired_users() -> int:
    """
    Finds suspended users past their scheduled_deletion_at date,
    anonymizes their PII, and marks them as deleted.
    Returns the count of users processed.
    """
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    processed = 0
    try:
        now = datetime.now()
        expired = (
            db.query(User)
            .filter(
                User.status == "suspended",
                User.scheduled_deletion_at <= now,
                User.deleted_at.is_(None),
            )
            .all()
        )

        for user in expired:
            logger.info(f"Anonymizing expired user id={user.id} (scheduled={user.scheduled_deletion_at})")
            user.full_name = f"משתמש לשעבר #{user.id}"
            user.email = f"deleted_{user.id}@removed.local"
            user.phone = None
            try:
                user.id_number = None
            except Exception:
                pass
            try:
                user.address = None
            except Exception:
                pass
            user.username = f"deleted_{user.id}"
            user.status = "deleted"
            user.is_active = False
            user.deleted_at = now

        if expired:
            db.commit()
            logger.info(f"Anonymized {len(expired)} expired user(s).")
        processed = len(expired)
    except Exception as e:
        logger.error(f"anonymize_expired_users failed: {e}")
        db.rollback()
    finally:
        db.close()

    return processed


async def schedule_nightly_cleanup():
    """
    Asyncio loop that runs anonymize_expired_users once per day (at ~midnight).
    Started from the FastAPI lifespan.
    """
    import asyncio as _asyncio
    from datetime import datetime as _dt, timedelta as _td

    while True:
        now = _dt.now()
        # Next midnight
        next_midnight = (_dt(now.year, now.month, now.day) + _td(days=1))
        seconds_until_midnight = (next_midnight - now).total_seconds()
        logger.info(f"[CRON] Next user cleanup in {seconds_until_midnight:.0f}s (at {next_midnight})")
        await _asyncio.sleep(seconds_until_midnight)
        try:
            count = anonymize_expired_users()
            logger.info(f"[CRON] Nightly cleanup done — {count} user(s) anonymized")
        except Exception as e:
            logger.error(f"[CRON] Nightly cleanup error: {e}")
