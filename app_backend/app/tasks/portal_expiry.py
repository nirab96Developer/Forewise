"""
CRON task: auto-expire supplier portal links and move to next supplier.
Runs every 10 minutes via the FastAPI lifespan scheduler.

Flow:
1. Find DISTRIBUTING work orders with expired portal_expiry
2. For forced supplier (is_forced) mark as expired, notify coordinator
3. For fair rotation auto-move to next supplier in same area with same equipment type
4. If no more suppliers mark as EXPIRED, notify coordinator
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def process_expired_portals() -> dict:
    """
    Find expired portal links and handle them.
    Returns stats: {expired_forced, rotated, no_supplier, errors}
    """
    from app.core.database import SessionLocal
    from app.models.work_order import WorkOrder
    from app.models.project import Project

    db = SessionLocal()
    stats = {"expired_forced": 0, "rotated": 0, "no_supplier": 0, "errors": 0}

    try:
        now = datetime.utcnow()

        expired_orders = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.status == "DISTRIBUTING",
                WorkOrder.portal_expiry < now,
            )
            .all()
        )

        if not expired_orders:
            return stats

        logger.info(f"[PORTAL_EXPIRY] Found {len(expired_orders)} expired portal links")

        for wo in expired_orders:
            try:
                is_forced = getattr(wo, 'is_forced', False) or getattr(wo, 'is_forced_selection', False)

                if is_forced:
                    wo.status = "EXPIRED"
                    wo.updated_at = now
                    wo.portal_token = None
                    _notify_coordinator(db, wo, "הספק שנבחר באילוץ לא הגיב בזמן. ההזמנה פגה.")
                    stats["expired_forced"] += 1
                    logger.info(f"[PORTAL_EXPIRY] WO {wo.id}: forced supplier expired")
                    continue

                # Fair rotation — find next supplier
                # Track ALL previously tried suppliers to prevent loop
                current_supplier_id = wo.supplier_id
                tried_suppliers = set()
                tried_suppliers.add(current_supplier_id)
                
                # Check rejection_notes for previously tried suppliers
                rejection_notes = getattr(wo, 'rejection_notes', '') or ''
                if 'tried:' in rejection_notes:
                    for sid in rejection_notes.split('tried:')[1].split(','):
                        try: tried_suppliers.add(int(sid.strip()))
                        except: pass
                
                area_id = None
                if wo.project_id:
                    project = db.query(Project).filter(Project.id == wo.project_id).first()
                    if project:
                        area_id = project.area_id

                next_supplier_id = _find_next_supplier(
                    db, wo, area_id, exclude_ids=tried_suppliers
                )

                if next_supplier_id:
                    # Save tried suppliers list to prevent future loops
                    tried_suppliers.add(next_supplier_id)
                    wo.rejection_notes = f"tried:{','.join(str(s) for s in tried_suppliers)}"
                    
                    _send_to_next_supplier(db, wo, next_supplier_id)
                    stats["rotated"] += 1
                    logger.info(
f"[PORTAL_EXPIRY] WO {wo.id}: rotated from supplier {current_supplier_id} {next_supplier_id} (tried: {tried_suppliers})"
                    )
                else:
                    wo.status = "EXPIRED"
                    wo.updated_at = now
                    wo.rejection_notes = f"tried:{','.join(str(s) for s in tried_suppliers)} — אין ספקים נוספים"
                    wo.portal_token = None
                    _notify_coordinator(
                        db, wo,
                        "לא נמצא ספק שאישר את ההזמנה לאחר סיום הסבב."
                    )
                    stats["no_supplier"] += 1
                    logger.info(f"[PORTAL_EXPIRY] WO {wo.id}: no more suppliers, expired")

            except Exception as e:
                logger.error(f"[PORTAL_EXPIRY] Error processing WO {wo.id}: {e}")
                stats["errors"] += 1

        db.commit()

    except Exception as e:
        logger.error(f"[PORTAL_EXPIRY] process_expired_portals failed: {e}")
        db.rollback()
    finally:
        db.close()

    return stats


def _find_next_supplier(db, work_order, area_id, exclude_id=None, exclude_ids=None):
    """Find next supplier in rotation who has equipment with license plate.
Hierarchy: area region None.
    Excludes all previously tried suppliers.
    """
    from app.models.supplier_rotation import SupplierRotation
    from app.models.supplier import Supplier
    from app.models.equipment import Equipment

    all_excluded = set(exclude_ids or set())
    if exclude_id:
        all_excluded.add(exclude_id)

    eq_type_id = getattr(work_order, 'equipment_type_id', None)
    if not eq_type_id and work_order.equipment_id:
        eq = db.query(Equipment).filter(Equipment.id == work_order.equipment_id).first()
        if eq:
            eq_type_id = getattr(eq, 'type_id', None)

    def search(filter_area_id=None, filter_region_id=None):
        query = (
            db.query(SupplierRotation)
            .join(Supplier, Supplier.id == SupplierRotation.supplier_id)
            .filter(
                SupplierRotation.is_active == True,
                SupplierRotation.is_available != False,
                Supplier.is_active == True,
            )
        )
        if all_excluded:
            query = query.filter(SupplierRotation.supplier_id.notin_(all_excluded))
        if eq_type_id:
            query = query.filter(SupplierRotation.equipment_type_id == eq_type_id)
        if filter_area_id:
            query = query.filter(SupplierRotation.area_id == filter_area_id)
        elif filter_region_id:
            query = query.filter(SupplierRotation.region_id == filter_region_id)

        for rot in query.order_by(SupplierRotation.rotation_position.asc()).all():
            eq_check = db.query(Equipment.id).filter(
                Equipment.supplier_id == rot.supplier_id,
                Equipment.is_active == True,
                Equipment.license_plate != None,
                Equipment.license_plate != '',
            )
            if eq_type_id:
                eq_check = eq_check.filter(Equipment.type_id == eq_type_id)
            if eq_check.first():
                return rot.supplier_id
        return None

    # Step 1: Same area
    if area_id:
        result = search(filter_area_id=area_id)
        if result:
            return result

    # Step 2: Same region
    region_id = None
    if work_order.project_id:
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == work_order.project_id).first()
        if project:
            region_id = project.region_id
    if region_id:
        result = search(filter_region_id=region_id)
        if result:
            return result

    return None


def _send_to_next_supplier(db, work_order, supplier_id):
    """Generate new portal token and send email to next supplier."""
    import secrets
    from datetime import timedelta

    work_order.supplier_id = supplier_id
    work_order.portal_token = secrets.token_urlsafe(32)
    work_order.portal_expiry = datetime.utcnow() + timedelta(hours=3)
    work_order.status = "DISTRIBUTING"
    work_order.updated_at = datetime.utcnow()

    portal_url = f"https://forewise.co/supplier-portal/{work_order.portal_token}"

    # Update rotation position
    from app.models.supplier_rotation import SupplierRotation
    rotation = (
        db.query(SupplierRotation)
        .filter(SupplierRotation.supplier_id == supplier_id)
        .first()
    )
    if rotation:
        rotation.total_assignments = (rotation.total_assignments or 0) + 1
        rotation.last_assignment_date = datetime.utcnow().date()
        if rotation.rotation_position is not None:
            rotation.rotation_position += 1

    # Send email
    try:
        from app.models.supplier import Supplier
        from app.core.email import send_email
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            to_email = supplier.email or supplier.contact_email
            if to_email:
                send_email(
                    to=to_email,
                    subject=f"הזמנת עבודה מספר {work_order.order_number} - דורש תגובה",
                    body=(
                        f"שלום {supplier.name},\n\n"
                        f"קיבלת הזמנת עבודה חדשה.\n"
                        f"הזמנה: {work_order.title or work_order.order_number}\n\n"
                        f"לצפייה ואישור/דחייה:\n{portal_url}\n\n"
                        f"הקישור תקף עד: {work_order.portal_expiry.strftime('%d/%m/%Y %H:%M')}\n\n"
                        "Forewise"
                    ),
                )
    except Exception as e:
        logger.warning(f"[PORTAL_EXPIRY] Failed to email supplier {supplier_id}: {e}")


def _notify_coordinator(db, work_order, message):
    """Send notification to coordinator about expired work order."""
    try:
        from app.services.notification_service import NotificationService
        from app.schemas.notification import NotificationCreate
        from sqlalchemy import text

        region_id = getattr(getattr(work_order, "project", None), "region_id", None)
        coordinators = db.execute(text("""
            SELECT u.id FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE r.code IN ('ORDER_COORDINATOR', 'ADMIN')
              AND (:region_id IS NULL OR r.code = 'ADMIN' OR u.region_id = :region_id)
              AND u.is_active = true
        """), {"region_id": region_id}).fetchall()

        ns = NotificationService()
        for row in coordinators:
            notif = NotificationCreate(
                user_id=row[0],
                title=f"הזמנה #{work_order.order_number} — פג תוקף",
                message=message,
                notification_type="WORK_ORDER",
                priority="high",
                entity_type="work_order",
                entity_id=work_order.id,
            )
            ns.create_notification(db, notif)
    except Exception as e:
        logger.warning(f"[PORTAL_EXPIRY] Notification failed for WO {work_order.id}: {e}")


async def schedule_portal_expiry_check():
    """
    Asyncio loop that checks for expired portal links every 10 minutes.
    Started from the FastAPI lifespan.
    """
    while True:
        await asyncio.sleep(600)  # 10 minutes
        try:
            stats = process_expired_portals()
            total = sum(stats.values())
            if total > 0:
                logger.info(f"[PORTAL_EXPIRY] Check complete: {stats}")
        except Exception as e:
            logger.error(f"[PORTAL_EXPIRY] Scheduled check failed: {e}")
