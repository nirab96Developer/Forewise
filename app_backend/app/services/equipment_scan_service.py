# app/services/equipment_scan_service.py
"""Equipment scanning and tracking service."""
import base64
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional

import qrcode
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.equipment import Equipment
from app.models.equipment_scan import EquipmentScan
from app.models.work_order import WorkOrder
from app.models.worklog import Worklog
from app.schemas.equipment_scan import ScanCreate, ScanUpdate


class EquipmentScanService:
    """Service for equipment scanning operations."""

    def get_scan(self, db: Session, scan_id: int) -> Optional[EquipmentScan]:
        """Get equipment scan by ID."""
        return (
            db.query(EquipmentScan)
            .options(
                joinedload(EquipmentScan.equipment),
                joinedload(EquipmentScan.scanned_by),
                joinedload(EquipmentScan.work_order),
            )
            .filter(and_(EquipmentScan.id == scan_id, EquipmentScan.is_active == True))
            .first()
        )

    def get_scans(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        equipment_id: Optional[int] = None,
        scanned_by: Optional[int] = None,
        scan_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[EquipmentScan]:
        """Get list of equipment scans with filters."""
        query = db.query(EquipmentScan).filter(EquipmentScan.is_active == True)

        if equipment_id:
            query = query.filter(EquipmentScan.equipment_id == equipment_id)
        if scanned_by:
            query = query.filter(EquipmentScan.scanned_by_id == scanned_by)
        if scan_type:
            query = query.filter(EquipmentScan.scan_type == scan_type)
        if start_date:
            query = query.filter(EquipmentScan.scan_time >= start_date)
        if end_date:
            query = query.filter(EquipmentScan.scan_time <= end_date)

        return (
            query.order_by(EquipmentScan.scan_time.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_scan(
        self,
        db: Session,
        scan_data: str,  # QR code or license plate
        scan_type: str,  # "qr", "license_plate", "manual"
        scanned_by_id: int,
        work_order_id: Optional[int] = None,
        location_lat: Optional[float] = None,
        location_lng: Optional[float] = None,
        notes: Optional[str] = None,
        validate_location: bool = True,
    ) -> EquipmentScan:
        """Create new equipment scan."""
        # Find equipment by scan data
        equipment = self._find_equipment_by_scan(db, scan_data, scan_type)
        if not equipment:
            raise ValueError("Equipment not found")

        # Validate work order if provided
        if work_order_id:
            work_order = (
                db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
            )

            if not work_order:
                raise ValueError("Work order not found")

            # Check if equipment matches work order
            if work_order.equipment_type:
                # Verify equipment type matches
                pass

        # Validate location if required
        if validate_location and location_lat and location_lng:
            if not self._validate_scan_location(
                db, equipment_id=equipment.id, lat=location_lat, lng=location_lng
            ):
                # Log warning but don't block
                notes = f"Location mismatch warning. {notes or ''}"

        # Create scan record
        db_scan = EquipmentScan(
            equipment_id=equipment.id,
            scan_type=scan_type,
            scan_data=scan_data,
            scanned_by_id=scanned_by_id,
            work_order_id=work_order_id,
            scan_time=datetime.utcnow(),
            location={"lat": location_lat, "lng": location_lng}
            if location_lat and location_lng
            else None,
            device_info=self._get_device_info(),
            notes=notes,
            is_verified=True,  # Can be set to False if verification needed
        )

        db.add(db_scan)

        # Update equipment last seen
        equipment.last_seen_at = datetime.utcnow()
        equipment.last_seen_by_id = scanned_by_id
        if location_lat and location_lng:
            equipment.last_location = {
                "lat": location_lat,
                "lng": location_lng,
                "timestamp": datetime.utcnow().isoformat(),
            }

        db.commit()
        db.refresh(db_scan)
        return db_scan

    def verify_scan(
        self,
        db: Session,
        scan_id: int,
        verified_by_id: int,
        is_valid: bool,
        verification_notes: Optional[str] = None,
    ) -> Optional[EquipmentScan]:
        """Verify equipment scan."""
        db_scan = self.get_scan(db, scan_id)
        if not db_scan:
            return None

        db_scan.is_verified = is_valid
        db_scan.verified_by_id = verified_by_id
        db_scan.verified_at = datetime.utcnow()
        db_scan.verification_notes = verification_notes
        db_scan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(db_scan)
        return db_scan

    def check_equipment_for_worklog(
        self, db: Session, user_id: int, work_order_id: int, report_date: date
    ) -> Dict[str, Any]:
        """Check if equipment was scanned for worklog."""
        # Get work order
        work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()

        if not work_order:
            return {"valid": False, "error": "Work order not found"}

        # Check for scans on the report date
        start_time = datetime.combine(report_date, datetime.min.time())
        end_time = datetime.combine(report_date, datetime.max.time())

        scans = (
            db.query(EquipmentScan)
            .filter(
                and_(
                    EquipmentScan.work_order_id == work_order_id,
                    EquipmentScan.scanned_by_id == user_id,
                    EquipmentScan.scan_time >= start_time,
                    EquipmentScan.scan_time <= end_time,
                    EquipmentScan.is_active == True,
                )
            )
            .all()
        )

        if not scans:
            return {"valid": False, "error": "No equipment scan found for this date"}

        return {
            "valid": True,
            "scan_count": len(scans),
            "first_scan": scans[0].scan_time.isoformat(),
            "last_scan": scans[-1].scan_time.isoformat() if len(scans) > 1 else None,
            "equipment_ids": list(set(s.equipment_id for s in scans)),
        }

    def generate_qr_code(self, db: Session, equipment_id: int) -> str:
        """Generate QR code for equipment."""
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

        if not equipment:
            raise ValueError("Equipment not found")

        # Generate QR data
        qr_data = f"EQ:{equipment.code}:{equipment_id}"

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # Update equipment with QR code
        equipment.qr_code = qr_data
        equipment.qr_generated_at = datetime.utcnow()
        db.commit()

        return f"data:image/png;base64,{img_str}"

    def get_equipment_tracking_history(
        self, db: Session, equipment_id: int, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get equipment tracking history."""
        cutoff = datetime.utcnow() - timedelta(days=days_back)

        scans = (
            db.query(EquipmentScan)
            .filter(
                and_(
                    EquipmentScan.equipment_id == equipment_id,
                    EquipmentScan.scan_time >= cutoff,
                    EquipmentScan.is_active == True,
                )
            )
            .order_by(EquipmentScan.scan_time.desc())
            .all()
        )

        history = []
        for scan in scans:
            history.append(
                {
                    "scan_id": scan.id,
                    "scan_time": scan.scan_time.isoformat(),
                    "scan_type": scan.scan_type,
                    "scanned_by_id": scan.scanned_by_id,
                    "work_order_id": scan.work_order_id,
                    "location": scan.location,
                    "is_verified": scan.is_verified,
                }
            )

        return history

    def get_scan_statistics(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        equipment_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get scan statistics."""
        query = db.query(EquipmentScan).filter(
            and_(
                EquipmentScan.scan_time >= start_date,
                EquipmentScan.scan_time <= end_date,
                EquipmentScan.is_active == True,
            )
        )

        if equipment_id:
            query = query.filter(EquipmentScan.equipment_id == equipment_id)

        scans = query.all()

        # Calculate statistics
        total_scans = len(scans)
        scan_types = {}
        daily_counts = {}
        unique_equipment = set()
        unique_users = set()

        for scan in scans:
            # Count by type
            if scan.scan_type not in scan_types:
                scan_types[scan.scan_type] = 0
            scan_types[scan.scan_type] += 1

            # Count by day
            day = scan.scan_time.date().isoformat()
            if day not in daily_counts:
                daily_counts[day] = 0
            daily_counts[day] += 1

            # Track unique items
            unique_equipment.add(scan.equipment_id)
            unique_users.add(scan.scanned_by_id)

        # Verification rate
        verified = len([s for s in scans if s.is_verified])
        verification_rate = (verified / total_scans * 100) if total_scans else 0

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_scans": total_scans,
            "unique_equipment": len(unique_equipment),
            "unique_users": len(unique_users),
            "by_type": scan_types,
            "by_day": daily_counts,
            "verification_rate": round(verification_rate, 2),
            "average_daily": total_scans / ((end_date - start_date).days + 1),
        }

    def _find_equipment_by_scan(
        self, db: Session, scan_data: str, scan_type: str
    ) -> Optional[Equipment]:
        """Find equipment by scan data."""
        if scan_type == "qr":
            # QR format: "EQ:CODE:ID"
            if scan_data.startswith("EQ:"):
                parts = scan_data.split(":")
                if len(parts) >= 3:
                    equipment_id = int(parts[2])
                    return (
                        db.query(Equipment).filter(Equipment.id == equipment_id).first()
                    )

            # Fallback to QR code field
            return db.query(Equipment).filter(Equipment.qr_code == scan_data).first()

        elif scan_type == "license_plate":
            return (
                db.query(Equipment).filter(Equipment.license_plate == scan_data).first()
            )

        elif scan_type == "manual":
            # Try code first, then license plate
            equipment = db.query(Equipment).filter(Equipment.code == scan_data).first()

            if not equipment:
                equipment = (
                    db.query(Equipment)
                    .filter(Equipment.license_plate == scan_data)
                    .first()
                )

            return equipment

        return None

    def _validate_scan_location(
        self,
        db: Session,
        equipment_id: int,
        lat: float,
        lng: float,
        max_distance_km: float = 5.0,
    ) -> bool:
        """Validate scan location against expected location."""
        equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()

        if not equipment or not equipment.location_id:
            return True  # Can't validate without location

        # Get expected location
        from app.models.location import Location

        location = (
            db.query(Location).filter(Location.id == equipment.location_id).first()
        )

        if not location or not location.coordinates:
            return True

        # Calculate distance (simplified)
        expected_lat = location.coordinates.get("lat")
        expected_lng = location.coordinates.get("lng")

        if not expected_lat or not expected_lng:
            return True

        # Haversine formula (simplified for small distances)
        import math

        R = 6371  # Earth radius in km

        dlat = math.radians(lat - expected_lat)
        dlng = math.radians(lng - expected_lng)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(expected_lat)
        ) * math.cos(math.radians(lat)) * math.sin(dlng / 2) * math.sin(dlng / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance <= max_distance_km

    def _get_device_info(self) -> Dict[str, Any]:
        """Get device information for scan."""
        # In production, this would get actual device info
        return {
            "platform": "mobile",
            "app_version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
