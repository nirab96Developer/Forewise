#!/usr/bin/env python3
"""Expire stale work orders — run via cron every 15 minutes."""
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("expire_orders")

try:
    from app.core.database import SessionLocal
    from app.services.work_order_service import WorkOrderService

    svc = WorkOrderService()
    db = SessionLocal()
    try:
        expired = svc.expire_work_orders(db)
        if expired:
            log.info(f"Expired {len(expired)} stale work orders: {[wo.id for wo in expired]}")
        else:
            log.info("No stale work orders to expire")
    finally:
        db.close()
except Exception as e:
    log.error(f"Expiration task failed: {e}")
    sys.exit(1)
