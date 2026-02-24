# /root/app_backend/app/schemas/report_run_summary.py - חדש (אופציונלי)
"""Report run summary schema."""
from decimal import Decimal
from typing import Dict

from pydantic import BaseModel, Field


class ReportRunSummary(BaseModel):
    """Report run summary statistics."""

    total_runs: int = 0

    # By status
    pending_count: int = 0
    running_count: int = 0
    completed_count: int = 0
    failed_count: int = 0
    cancelled_count: int = 0
    timeout_count: int = 0

    # Performance
    total_execution_time: int = 0
    average_execution_time: float = 0.0
    total_rows_processed: int = 0

    # Success rate
    success_rate: float = 0.0
    failure_rate: float = 0.0

    # By report
    by_report: Dict[str, int] = Field(default_factory=dict)

    # By user
    by_user: Dict[str, int] = Field(default_factory=dict)
