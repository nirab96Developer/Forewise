"""
Invoice ↔ Work Order link service.

Thin wrapper around the `invoice_work_orders` table. Centralises:
  * link creation when an invoice is generated
  * lookup of WOs paid by an invoice (and reverse: invoices that paid a WO)
  * the per-WO money split used by mark-paid for budget settlement

Every other module reaches into the link table through this service so the
shape of the join is owned in one place.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Iterable, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.invoice_item import InvoiceItem
from app.models.invoice_work_order import InvoiceWorkOrder
from app.models.worklog import Worklog

logger = logging.getLogger(__name__)


def _zero() -> Decimal:
    return Decimal("0")


def link_invoice_to_work_orders(
    db: Session, invoice_id: int,
) -> List[InvoiceWorkOrder]:
    """Compute and persist the WO links for an invoice from its line items.

    Idempotent — existing rows for the same (invoice, wo) are updated, not
    duplicated. Safe to call multiple times during the invoice's lifecycle.

    Returns the resulting links.
    """
    rows = (
        db.query(
            Worklog.work_order_id.label("wo_id"),
            func.coalesce(
                func.sum(func.coalesce(InvoiceItem.total, InvoiceItem.total_price, 0)),
                0,
            ).label("amount"),
        )
        .join(InvoiceItem, InvoiceItem.worklog_id == Worklog.id)
        .filter(
            InvoiceItem.invoice_id == invoice_id,
            InvoiceItem.deleted_at.is_(None),
            Worklog.work_order_id.isnot(None),
        )
        .group_by(Worklog.work_order_id)
        .all()
    )

    if not rows:
        return []

    # Upsert each row.
    results: List[InvoiceWorkOrder] = []
    for r in rows:
        existing = (
            db.query(InvoiceWorkOrder)
            .filter(
                InvoiceWorkOrder.invoice_id == invoice_id,
                InvoiceWorkOrder.work_order_id == r.wo_id,
            )
            .first()
        )
        if existing:
            existing.allocated_amount = Decimal(str(r.amount or 0))
        else:
            existing = InvoiceWorkOrder(
                invoice_id=invoice_id,
                work_order_id=r.wo_id,
                allocated_amount=Decimal(str(r.amount or 0)),
            )
            db.add(existing)
        results.append(existing)

    db.flush()
    return results


def list_work_orders_for_invoice(
    db: Session, invoice_id: int,
) -> List[Tuple[int, Decimal]]:
    """Return [(work_order_id, allocated_amount), ...] for an invoice."""
    rows = (
        db.query(
            InvoiceWorkOrder.work_order_id,
            InvoiceWorkOrder.allocated_amount,
        )
        .filter(
            InvoiceWorkOrder.invoice_id == invoice_id,
            InvoiceWorkOrder.deleted_at.is_(None),
        )
        .all()
    )
    return [(r[0], Decimal(str(r[1] or 0))) for r in rows]


def list_invoices_for_work_order(
    db: Session, work_order_id: int,
) -> List[Tuple[int, Decimal]]:
    """Return [(invoice_id, allocated_amount), ...] for a work order."""
    rows = (
        db.query(
            InvoiceWorkOrder.invoice_id,
            InvoiceWorkOrder.allocated_amount,
        )
        .filter(
            InvoiceWorkOrder.work_order_id == work_order_id,
            InvoiceWorkOrder.deleted_at.is_(None),
        )
        .all()
    )
    return [(r[0], Decimal(str(r[1] or 0))) for r in rows]


def split_payment_across_work_orders(
    db: Session, invoice_id: int, paid_amount: Decimal,
) -> List[Tuple[int, Decimal]]:
    """Distribute ``paid_amount`` across the WOs of this invoice in
    proportion to their `allocated_amount`. Last WO absorbs the rounding
    remainder so the sum exactly equals ``paid_amount``.

    If no link rows exist, returns an empty list and the caller should
    fall back to invoice_items derivation (only happens for legacy data
    that hasn't been backfilled).
    """
    paid_amount = Decimal(str(paid_amount or 0))
    links = list_work_orders_for_invoice(db, invoice_id)
    if not links:
        return []

    total = sum((amt for _, amt in links), _zero())
    if total <= 0:
        # Avoid div-by-zero — split evenly.
        share = (paid_amount / len(links)).quantize(Decimal("0.01"))
        result = [(wo, share) for wo, _ in links[:-1]]
        accumulated = sum((s for _, s in result), _zero())
        result.append((links[-1][0], paid_amount - accumulated))
        return result

    out: List[Tuple[int, Decimal]] = []
    for wo, amt in links[:-1]:
        share = (amt / total * paid_amount).quantize(Decimal("0.01"))
        out.append((wo, share))
    last_wo = links[-1][0]
    accumulated = sum((s for _, s in out), _zero())
    out.append((last_wo, paid_amount - accumulated))
    return out
