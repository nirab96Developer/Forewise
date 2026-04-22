"""
CRON task: prune stale OTP tokens.

We accumulate one row per login attempt + one per resend; an audit found
107+ tokens older than 7 days and 46 active-but-expired in production.
Without cleanup the table grows unbounded and the OTP lookup gets slower
the longer the system runs.

Runs nightly (offset by an hour from the user-lifecycle task to spread
DB load) via the FastAPI lifespan scheduler.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.otp_token import OTPToken

logger = logging.getLogger(__name__)


def cleanup_expired_otp_tokens() -> dict:
    """
    Two passes:

    1. Hard-delete tokens that are older than 30 days OR were used / are
       inactive AND older than 7 days. They serve no auditing purpose.
    2. Mark active-but-expired tokens as `is_active = False` so any future
       resend logic doesn't accidentally treat them as candidates.

    Returns counts so the scheduler can log activity.
    """
    db = SessionLocal()
    deleted = 0
    deactivated = 0
    try:
        now = datetime.utcnow()
        hard_cutoff = now - timedelta(days=30)
        soft_cutoff = now - timedelta(days=7)

        # 1. Hard delete very old or already-consumed tokens.
        deleted = (
            db.query(OTPToken)
            .filter(
                (OTPToken.created_at < hard_cutoff)
                | (
                    (OTPToken.created_at < soft_cutoff)
                    & (
                        (OTPToken.is_used == True)
                        | (OTPToken.is_active == False)
                    )
                )
            )
            .delete(synchronize_session=False)
        )

        # 2. Deactivate active-but-expired tokens.
        deactivated = (
            db.query(OTPToken)
            .filter(
                OTPToken.is_active == True,
                OTPToken.expires_at < now,
            )
            .update({OTPToken.is_active: False}, synchronize_session=False)
        )

        db.commit()
    except Exception as e:
        logger.error(f"[OTP_CLEANUP] Failed: {e}")
        db.rollback()
    finally:
        db.close()
    return {"deleted": deleted, "deactivated": deactivated}


async def schedule_otp_cleanup():
    """
    Asyncio loop that runs the OTP cleanup once per day, offset 1h from the
    nightly-cleanup boundary so the two cron tasks don't pile on the DB at
    the same minute.
    """
    # Initial delay so we don't race during process startup.
    await asyncio.sleep(60 * 60)  # 1 hour
    while True:
        try:
            stats = cleanup_expired_otp_tokens()
            if stats.get("deleted") or stats.get("deactivated"):
                logger.info(f"[OTP_CLEANUP] {stats}")
        except Exception as e:
            logger.error(f"[OTP_CLEANUP] Scheduled run failed: {e}")
        await asyncio.sleep(24 * 60 * 60)  # 24 hours
