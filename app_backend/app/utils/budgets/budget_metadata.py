# app/models/budget/utils/budget_metadata.py
import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class BudgetMetadataKeys(str, Enum):
    """מפתחות metadata לתקציב"""

    ALLOCATIONS = "allocations"
    TRANSFERS = "transfers"
    RELEASES = "releases"
    STATUS_CHANGES = "status_changes"
    APPROVALS = "approvals"
    REJECTIONS = "rejections"
    NOTES = "notes"
    ALERTS = "alerts"
    AUDIT_TRAIL = "audit_trail"
    AMOUNT_CHANGES = "amount_changes"
    COMMITMENTS = "commitments"
    EXPENSES = "expenses"
    PRICE_HISTORY = "price_history"
    QUANTITY_CHANGES = "quantity_changes"
    FREEZE_HISTORY = "freeze_history"
    UNLOCK_HISTORY = "unlock_history"
    ATTACHMENTS = "attachments"
    EXTERNAL_REFERENCES = "external_references"


class BudgetMetadataManager:
    """מנהל מטא-דאטה לתקציבים ופריטי תקציב"""

    @staticmethod
    def _ensure_list(metadata: Dict[str, Any], key: str) -> List[Any]:
        """וידוא שהערך הוא רשימה"""
        if key not in metadata:
            metadata[key] = []
        elif not isinstance(metadata[key], list):
            logger.warning(f"Key {key} is not a list, converting to list")
            metadata[key] = [metadata[key]]
        return metadata[key]

    @staticmethod
    def record_status_change(
        metadata: Dict[str, Any],
        old_status: str,
        new_status: str,
        key: str,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """תיעוד שינוי סטטוס"""
        status_list = BudgetMetadataManager._ensure_list(metadata, key)

        status_list.append(
            {
                "from": old_status,
                "to": new_status,
                "date": datetime.now(timezone.utc).isoformat(),
                "by_user_id": user_id,
                "reason": reason,
            }
        )

        return metadata

    @staticmethod
    def record_price_change(
        metadata: Dict[str, Any],
        old_price: float,
        new_price: float,
        key: str,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """תיעוד שינוי מחיר"""
        price_list = BudgetMetadataManager._ensure_list(metadata, key)

        change_percent = 0
        if old_price > 0:
            change_percent = round((new_price - old_price) / old_price * 100, 2)

        price_list.append(
            {
                "old_price": old_price,
                "new_price": new_price,
                "change_percent": change_percent,
                "date": datetime.now(timezone.utc).isoformat(),
                "by_user_id": user_id,
                "reason": reason,
            }
        )

        return metadata

    @staticmethod
    def record_quantity_change(
        metadata: Dict[str, Any],
        old_quantity: float,
        new_quantity: float,
        key: str,
        user_id: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """תיעוד שינוי כמות"""
        quantity_list = BudgetMetadataManager._ensure_list(metadata, key)

        change_percent = 0
        if old_quantity > 0:
            change_percent = round(
                (new_quantity - old_quantity) / old_quantity * 100, 2
            )

        quantity_list.append(
            {
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "change_percent": change_percent,
                "date": datetime.now(timezone.utc).isoformat(),
                "by_user_id": user_id,
                "reason": reason,
            }
        )

        return metadata

    @staticmethod
    def add_note(
        metadata: Dict[str, Any],
        note: str,
        key: str,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        added_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """הוספת הערה"""
        notes_list = BudgetMetadataManager._ensure_list(metadata, key)

        # תמיכה בשני שמות פרמטרים לצורך תאימות
        final_user_id = user_id or added_by_id

        notes_list.append(
            {
                "text": note,
                "added_by_id": final_user_id,
                "date": datetime.now(timezone.utc).isoformat(),
                "category": category,
                "priority": priority,
            }
        )

        return metadata

    @staticmethod
    def add_allocation(
        metadata: Dict[str, Any],
        amount: float,
        description: Optional[str],
        key: str,
        allocation_id: Optional[str] = None,
        balance_after: Optional[float] = None,
        project_id: Optional[int] = None,
        item_id: Optional[int] = None,
        user_id: Optional[int] = None,
        allocation_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """הוספת הקצאה"""
        allocations_list = BudgetMetadataManager._ensure_list(metadata, key)

        allocation_record = {
            "id": allocation_id or f"ALLOC-{datetime.now().timestamp()}",
            "amount": amount,
            "description": description,
            "date": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }

        if balance_after is not None:
            allocation_record["balance_after"] = balance_after

        if project_id is not None:
            allocation_record["project_id"] = project_id

        if item_id is not None:
            allocation_record["item_id"] = item_id

        if user_id is not None:
            allocation_record["user_id"] = user_id

        if allocation_type is not None:
            allocation_record["allocation_type"] = allocation_type

        if notes is not None:
            allocation_record["notes"] = notes

        allocations_list.append(allocation_record)
        return metadata

    @staticmethod
    def add_commitment(
        metadata: Dict[str, Any],
        amount: float,
        reference: Optional[str],
        key: str,
        vendor_id: Optional[int] = None,
        expected_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """הוספת התחייבות"""
        commitments_list = BudgetMetadataManager._ensure_list(metadata, key)

        commitment_record = {
            "amount": amount,
            "reference": reference,
            "date": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }

        if vendor_id is not None:
            commitment_record["vendor_id"] = vendor_id

        if expected_date is not None:
            commitment_record["expected_date"] = expected_date.isoformat()

        commitments_list.append(commitment_record)
        return metadata

    @staticmethod
    def add_expense(
        metadata: Dict[str, Any],
        amount: float,
        invoice_ref: Optional[str] = None,
        key: str = BudgetMetadataKeys.EXPENSES.value,
        vendor_id: Optional[int] = None,
        payment_method: Optional[str] = None,
        expense_category: Optional[str] = None,
        description: Optional[str] = None,
        expense_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """הוספת הוצאה"""
        expenses_list = BudgetMetadataManager._ensure_list(metadata, key)

        expense_record = {
            "amount": amount,
            "invoice_ref": invoice_ref,
            "date": datetime.now(timezone.utc).isoformat(),
            "status": "paid",
        }

        if vendor_id is not None:
            expense_record["vendor_id"] = vendor_id

        if payment_method is not None:
            expense_record["payment_method"] = payment_method

        if expense_category is not None:
            expense_record["category"] = expense_category

        if description is not None:
            expense_record["description"] = description

        if expense_type is not None:
            expense_record["expense_type"] = expense_type

        expenses_list.append(expense_record)
        return metadata

    @staticmethod
    def add_alert(
        metadata: Dict[str, Any],
        alert_type: str,
        message: str,
        severity: str = "medium",
        key: str = BudgetMetadataKeys.ALERTS.value,
        auto_generated: bool = True,
    ) -> Dict[str, Any]:
        """הוספת התראה"""
        alerts_list = BudgetMetadataManager._ensure_list(metadata, key)

        alerts_list.append(
            {
                "type": alert_type,
                "message": message,
                "severity": severity,
                "date": datetime.now(timezone.utc).isoformat(),
                "auto_generated": auto_generated,
                "acknowledged": False,
            }
        )

        return metadata

    @staticmethod
    def acknowledge_alert(
        metadata: Dict[str, Any],
        alert_index: int,
        acknowledged_by_id: int,
        key: str = BudgetMetadataKeys.ALERTS.value,
    ) -> Dict[str, Any]:
        """אישור קריאת התראה"""
        alerts_list = metadata.get(key, [])

        if 0 <= alert_index < len(alerts_list):
            alerts_list[alert_index]["acknowledged"] = True
            alerts_list[alert_index]["acknowledged_by_id"] = acknowledged_by_id
            alerts_list[alert_index]["acknowledged_at"] = datetime.now(
                timezone.utc
            ).isoformat()

        return metadata

    @staticmethod
    def add_attachment(
        metadata: Dict[str, Any],
        file_name: str,
        file_path: str,
        file_size: int,
        file_type: str,
        uploaded_by_id: int,
        key: str = BudgetMetadataKeys.ATTACHMENTS.value,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """הוספת קובץ מצורף"""
        attachments_list = BudgetMetadataManager._ensure_list(metadata, key)

        attachments_list.append(
            {
                "file_name": file_name,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "uploaded_by_id": uploaded_by_id,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "description": description,
            }
        )

        return metadata

    @staticmethod
    def add_external_reference(
        metadata: Dict[str, Any],
        ref_type: str,
        ref_id: str,
        ref_system: str,
        key: str = BudgetMetadataKeys.EXTERNAL_REFERENCES.value,
        ref_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """הוספת הפניה חיצונית"""
        refs_list = BudgetMetadataManager._ensure_list(metadata, key)

        refs_list.append(
            {
                "type": ref_type,
                "id": ref_id,
                "system": ref_system,
                "url": ref_url,
                "added_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return metadata

    @staticmethod
    def get_latest_status_change(
        metadata: Dict[str, Any], key: str
    ) -> Optional[Dict[str, Any]]:
        """קבלת שינוי הסטטוס האחרון"""
        status_changes = metadata.get(key, [])
        return status_changes[-1] if status_changes else None

    @staticmethod
    def get_total_allocations(
        metadata: Dict[str, Any],
        key: str = BudgetMetadataKeys.ALLOCATIONS.value,
        active_only: bool = True,
    ) -> float:
        """חישוב סך ההקצאות"""
        allocations = metadata.get(key, [])

        if active_only:
            allocations = [
                a for a in allocations if a.get("status", "active") == "active"
            ]

        return sum(a.get("amount", 0) for a in allocations)

    @staticmethod
    def get_total_commitments(
        metadata: Dict[str, Any],
        key: str = BudgetMetadataKeys.COMMITMENTS.value,
        pending_only: bool = True,
    ) -> float:
        """חישוב סך ההתחייבויות"""
        commitments = metadata.get(key, [])

        if pending_only:
            commitments = [
                c for c in commitments if c.get("status", "pending") == "pending"
            ]

        return sum(c.get("amount", 0) for c in commitments)

    @staticmethod
    def get_total_expenses(
        metadata: Dict[str, Any],
        key: str = BudgetMetadataKeys.EXPENSES.value,
        by_category: bool = False,
    ) -> Union[float, Dict[str, float]]:
        """חישוב סך ההוצאות"""
        expenses = metadata.get(key, [])

        if by_category:
            category_totals = {}
            for expense in expenses:
                category = expense.get("category", "uncategorized")
                amount = expense.get("amount", 0)
                category_totals[category] = category_totals.get(category, 0) + amount
            return category_totals

        return sum(e.get("amount", 0) for e in expenses)

    @staticmethod
    def get_expenses(
        metadata: Dict[str, Any], key: str = BudgetMetadataKeys.EXPENSES.value
    ) -> List[Dict[str, Any]]:
        """קבלת רשימת הוצאות"""
        return metadata.get(key, [])

    @staticmethod
    def get_unacknowledged_alerts(
        metadata: Dict[str, Any], key: str = BudgetMetadataKeys.ALERTS.value
    ) -> List[Dict[str, Any]]:
        """קבלת התראות שלא אושרו"""
        alerts = metadata.get(key, [])
        return [a for a in alerts if not a.get("acknowledged", False)]

    @staticmethod
    def search_notes(
        metadata: Dict[str, Any],
        search_text: str,
        key: str = BudgetMetadataKeys.NOTES.value,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """חיפוש בהערות"""
        notes = metadata.get(key, [])
        results = []

        search_text_lower = search_text.lower()

        for note in notes:
            # סינון לפי קטגוריה אם נדרש
            if category_filter and note.get("category") != category_filter:
                continue

            # חיפוש בטקסט
            if search_text_lower in note.get("text", "").lower():
                results.append(note)

        return results

    @staticmethod
    def cleanup_old_entries(
        metadata: Dict[str, Any], key: str, days_to_keep: int = 365
    ) -> Dict[str, Any]:
        """ניקוי רשומות ישנות"""
        if key not in metadata:
            return metadata

        entries = metadata[key]
        if not isinstance(entries, list):
            return metadata

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

        # סינון רשומות חדשות
        new_entries = []
        for entry in entries:
            entry_date_str = (
                entry.get("date") or entry.get("uploaded_at") or entry.get("added_at")
            )
            if entry_date_str:
                try:
                    entry_date = datetime.fromisoformat(
                        entry_date_str.replace("Z", "+00:00")
                    )
                    if entry_date >= cutoff_date:
                        new_entries.append(entry)
                except (ValueError, AttributeError):
                    # שמור רשומות עם תאריך לא תקין
                    new_entries.append(entry)
            else:
                # שמור רשומות ללא תאריך
                new_entries.append(entry)

        metadata[key] = new_entries
        return metadata

    @staticmethod
    def merge_metadata(
        base_metadata: Dict[str, Any],
        new_metadata: Dict[str, Any],
        list_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """מיזוג metadata - שימושי למיזוג שינויים"""
        result = base_metadata.copy()

        if list_keys is None:
            list_keys = [key.value for key in BudgetMetadataKeys]

        for key, value in new_metadata.items():
            if key in list_keys and isinstance(value, list):
                # מיזוג רשימות
                existing = result.get(key, [])
                if isinstance(existing, list):
                    result[key] = existing + value
                else:
                    result[key] = value
            else:
                # החלפת ערכים רגילים
                result[key] = value

        return result

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """בדיקת תקינות metadata"""
        errors = []

        # בדיקת מבנה בסיסי
        if not isinstance(metadata, dict):
            errors.append("Metadata must be a dictionary")
            return False, errors

        # בדיקת שדות רשימה
        list_fields = [key.value for key in BudgetMetadataKeys]

        for field in list_fields:
            if field in metadata and not isinstance(metadata[field], list):
                errors.append(f"Field '{field}' must be a list")

        # בדיקת תאריכים
        date_fields = ["date", "uploaded_at", "added_at", "acknowledged_at"]

        for key, value in metadata.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        for date_field in date_fields:
                            if date_field in item:
                                try:
                                    datetime.fromisoformat(
                                        item[date_field].replace("Z", "+00:00")
                                    )
                                except (ValueError, AttributeError):
                                    errors.append(
                                        f"Invalid date format in {key}.{date_field}: {item[date_field]}"
                                    )

        return len(errors) == 0, errors

    @staticmethod
    def export_to_json(metadata: Dict[str, Any], pretty: bool = True) -> str:
        """ייצוא metadata ל-JSON"""
        if pretty:
            return json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)
        return json.dumps(metadata, ensure_ascii=False)

    @staticmethod
    def import_from_json(json_str: str) -> Dict[str, Any]:
        """ייבוא metadata מ-JSON"""
        try:
            metadata = json.loads(json_str)
            is_valid, errors = BudgetMetadataManager.validate_metadata(metadata)
            if not is_valid:
                logger.warning(f"Imported metadata has validation errors: {errors}")
            return metadata
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return {}
