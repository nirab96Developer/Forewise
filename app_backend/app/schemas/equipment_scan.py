# /root/app_backend/app/schemas/equipment_scan.py - חדש
"""Equipment scan schemas - Aligned with database model."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ScanType(str, Enum):
    """Scan type enum - matches model."""

    QR = "qr"
    LICENSE = "license"
    MANUAL = "manual"


class MatchStatus(str, Enum):
    """Match status enum - matches model."""

    MATCHED = "matched"
    MISMATCH = "mismatch"
    DIFFERENT = "different"
    APPROVED = "approved"


class EquipmentScanBase(BaseModel):
    """Base equipment scan schema."""

    equipment_id: int = Field(..., gt=0, description="Equipment ID")
    work_order_id: int = Field(..., gt=0, description="Work order ID")

    scan_type: ScanType = Field(..., description="Type of scan")
    scanned_value: str = Field(
        ..., min_length=1, max_length=100, description="Scanned value"
    )
    expected_value: Optional[str] = Field(
        None, max_length=100, description="Expected value"
    )

    action_taken: Optional[str] = Field(
        None, max_length=50, description="Action taken on mismatch"
    )


class EquipmentScanCreate(EquipmentScanBase):
    """Create equipment scan schema."""

    scanned_by_id: int = Field(..., gt=0, description="User who scanned")
    scanned_at: datetime = Field(default_factory=datetime.utcnow)
    match_status: MatchStatus = Field(..., description="Match status")


class EquipmentScanUpdate(BaseModel):
    """Update equipment scan schema."""

    action_taken: Optional[str] = Field(None, max_length=50)
    approval_notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class EquipmentScanApproval(BaseModel):
    """Approve equipment scan mismatch."""

    approval_notes: str = Field(..., min_length=1, max_length=500)


class EquipmentScanResponse(EquipmentScanBase):
    """Equipment scan response schema."""

    id: int
    match_status: MatchStatus

    # Scan metadata
    scanned_by_id: int
    scanned_at: datetime

    # Approval (if mismatch)
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    is_matched: bool = False
    needs_approval: bool = False
    is_approved: bool = False

    # From relationships
    equipment_name: Optional[str] = None
    equipment_code: Optional[str] = None
    work_order_number: Optional[str] = None
    scanned_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.is_matched = self.match_status == MatchStatus.MATCHED
        self.needs_approval = self.match_status in [
            MatchStatus.MISMATCH,
            MatchStatus.DIFFERENT,
        ]
        self.is_approved = (
            self.match_status == MatchStatus.APPROVED or self.approved_by_id is not None
        )


class EquipmentScanFilter(BaseModel):
    """Filter for equipment scans."""

    equipment_id: Optional[int] = None
    work_order_id: Optional[int] = None
    scan_type: Optional[ScanType] = None
    match_status: Optional[MatchStatus] = None
    scanned_by_id: Optional[int] = None
    approved_by_id: Optional[int] = None
    scanned_from: Optional[datetime] = None
    scanned_to: Optional[datetime] = None
    needs_approval: Optional[bool] = None
    is_approved: Optional[bool] = None


class EquipmentScanSummary(BaseModel):
    """Equipment scan summary statistics."""

    total_scans: int = 0

    # By scan type
    qr_scans: int = 0
    license_scans: int = 0
    manual_scans: int = 0

    # By match status
    matched_count: int = 0
    mismatch_count: int = 0
    different_count: int = 0
    approved_count: int = 0

    # Approval metrics
    pending_approval: int = 0
    approval_rate: float = 0.0

    # Period
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class ScanStatistics(BaseModel):
    """Scan statistics schema."""
    
    total_scans: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    pending_scans: int = 0
    success_rate: float = 0.0
    
    # By type
    qr_scans: int = 0
    license_scans: int = 0
    manual_scans: int = 0
    
    # By status
    matched_scans: int = 0
    mismatch_scans: int = 0
    approved_scans: int = 0
    
    # Time period
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ScanVerification(BaseModel):
    """Scan verification schema."""
    
    scanned_value: str = Field(..., min_length=1, max_length=100)
    expected_value: Optional[str] = Field(None, max_length=100)
    verification_result: str = Field(..., description="Verification result")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)


# Alias for compatibility
ScanCreate = EquipmentScanCreate
ScanUpdate = EquipmentScanUpdate
ScanResponse = EquipmentScanResponse