#!/usr/bin/env python3
"""DEPRECATED — replaced by app/tasks/portal_expiry.py.

The expiry of supplier-portal tokens is now handled by an in-process scheduler
that ships with the FastAPI app (started in main.py lifespan, see
``schedule_portal_expiry_check``). This script used to query the obsolete
``sent_to_supplier`` status and is therefore a no-op.

If you still have a crontab entry calling this file, please remove it — running
two expiry mechanisms in parallel can corrupt rotation order.
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("expire_orders")

log.warning(
    "run_expire_orders.py is DEPRECATED. Expiry runs in-process via "
    "app/tasks/portal_expiry.py. Remove this cron entry."
)
sys.exit(0)
