# app/utils/budgets/balance_release_type.py
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Enums
class ReleaseTypeEnum(str, Enum):
    """סוגי שחרור תקציב"""

    REGULAR = "regular"  # שחרור רגיל
    EMERGENCY = "emergency"  # שחרור חירום
    SCHEDULED = "scheduled"  # שחרור מתוזמן
    MILESTONE = "milestone"  # שחרור לפי אבן דרך
    PERCENTAGE = "percentage"  # שחרור לפי אחוז
    CONDITIONAL = "conditional"  # שחרור מותנה
    ADVANCE = "advance"  # מקדמה
    FINAL = "final"  # שחרור סופי


class ReleaseStatusEnum(str, Enum):
    """סטטוסי שחרור"""

    DRAFT = "draft"  # טיוטה
    PENDING = "pending"  # ממתין לאישור
    APPROVED = "approved"  # מאושר
    REJECTED = "rejected"  # נדחה
    PROCESSING = "processing"  # בעיבוד
    COMPLETED = "completed"  # הושלם
    CANCELLED = "cancelled"  # בוטל
    ON_HOLD = "on_hold"  # מושהה
    EXPIRED = "expired"  # פג תוקף


class ReleaseFrequencyEnum(str, Enum):
    """תדירות שחרור לשחרורים חוזרים"""

    ONCE = "once"  # חד פעמי
    WEEKLY = "weekly"  # שבועי
    BIWEEKLY = "biweekly"  # דו-שבועי
    MONTHLY = "monthly"  # חודשי
    QUARTERLY = "quarterly"  # רבעוני
    SEMI_ANNUAL = "semi_annual"  # חצי שנתי
    YEARLY = "yearly"  # שנתי


class ReleaseCalculationMethod(str, Enum):
    """שיטת חישוב שחרור"""

    FIXED_AMOUNT = "fixed_amount"  # סכום קבוע
    PERCENTAGE = "percentage"  # אחוז מהתקציב
    FORMULA = "formula"  # נוסחה מותאמת
    MILESTONE_BASED = "milestone"  # לפי אבני דרך
    USAGE_BASED = "usage"  # לפי שימוש
    PERFORMANCE_BASED = "performance"  # לפי ביצועים


# Dataclasses
@dataclass
class ReleaseRule:
    """חוק שחרור תקציב"""

    rule_type: str
    condition: str
    value: Any
    description: Optional[str] = None
    is_mandatory: bool = True

    def validate(self, context: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """בדיקת תקינות החוק"""
        try:
            if self.rule_type == "min_percentage":
                current_percentage = context.get("utilization_rate", 0)
                if current_percentage < self.value:
                    return (
                        False,
                        f"ניצול נוכחי {current_percentage}% נמוך מהנדרש {self.value}%",
                    )

            elif self.rule_type == "max_amount":
                requested = context.get("requested_amount", 0)
                if requested > self.value:
                    return False, f"סכום מבוקש {requested} גבוה מהמותר {self.value}"

            elif self.rule_type == "time_constraint":
                # בדיקת מגבלות זמן
                pass

            return True, None

        except Exception as e:
            logger.error(f"Error validating rule: {str(e)}")
            return False, str(e)


@dataclass
class ReleaseCondition:
    """תנאי לשחרור תקציב"""

    condition_type: str
    required_value: Any
    current_value: Optional[Any] = None
    is_met: bool = False
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None
    notes: Optional[str] = None

    def check_condition(
        self, current_value: Any, user_id: Optional[int] = None
    ) -> bool:
        """בדיקת עמידה בתנאי"""
        self.current_value = current_value
        self.checked_at = datetime.now(timezone.utc)
        self.checked_by = user_id

        if self.condition_type == "approval":
            self.is_met = bool(current_value)
        elif self.condition_type == "minimum_progress":
            self.is_met = current_value >= self.required_value
        elif self.condition_type == "document_submitted":
            self.is_met = bool(current_value)
        elif self.condition_type == "date_reached":
            self.is_met = datetime.now(timezone.utc) >= self.required_value

        return self.is_met


@dataclass
class ReleaseTemplate:
    """תבנית שחרור"""

    template_id: str
    name: str
    description: str
    release_type: ReleaseTypeEnum
    calculation_method: ReleaseCalculationMethod
    default_percentage: Optional[float] = None
    default_amount: Optional[float] = None
    rules: List[ReleaseRule] = field(default_factory=list)
    conditions: List[ReleaseCondition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """המרה למילון"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "release_type": self.release_type.value,
            "calculation_method": self.calculation_method.value,
            "default_percentage": self.default_percentage,
            "default_amount": self.default_amount,
            "rules_count": len(self.rules),
            "conditions_count": len(self.conditions),
            "metadata": self.metadata,
        }


@dataclass
class ReleaseApprovalLevel:
    """רמת אישור לשחרור"""

    level: int
    role_required: str
    min_amount: float
    max_amount: float
    description: str
    require_justification: bool = True
    require_attachments: bool = False

    def is_applicable(self, amount: float) -> bool:
        """בדיקה האם הרמה רלוונטית לסכום"""
        return self.min_amount <= amount <= self.max_amount


# Helper Functions
def get_release_rules(release_type: str) -> List[ReleaseRule]:
    """קבלת חוקי שחרור לפי סוג"""
    rules = []

    if release_type == ReleaseTypeEnum.REGULAR.value:
        rules.extend(
            [
                ReleaseRule(
                    rule_type="min_percentage",
                    condition="utilization >= 70%",
                    value=70,
                    description="ניצול מינימלי של 70% מהשחרור הקודם",
                ),
                ReleaseRule(
                    rule_type="max_amount",
                    condition="amount <= budget * 0.25",
                    value=0.25,
                    description="עד 25% מהתקציב בכל שחרור",
                    is_mandatory=True,
                ),
            ]
        )

    elif release_type == ReleaseTypeEnum.EMERGENCY.value:
        rules.append(
            ReleaseRule(
                rule_type="justification",
                condition="emergency_justification",
                value=True,
                description="נדרש נימוק חירום מפורט",
                is_mandatory=True,
            )
        )

    elif release_type == ReleaseTypeEnum.MILESTONE.value:
        rules.append(
            ReleaseRule(
                rule_type="milestone_completion",
                condition="milestone_completed",
                value=True,
                description="אבן דרך חייבת להיות מושלמת",
                is_mandatory=True,
            )
        )

    return rules


def get_approval_levels() -> List[ReleaseApprovalLevel]:
    """קבלת רמות אישור"""
    return [
        ReleaseApprovalLevel(
            level=1,
            role_required="project_manager",
            min_amount=0,
            max_amount=50000,
            description="מנהל פרויקט - עד 50K",
        ),
        ReleaseApprovalLevel(
            level=2,
            role_required="area_manager",
            min_amount=50001,
            max_amount=250000,
            description="מנהל אזור - 50K-250K",
            require_justification=True,
        ),
        ReleaseApprovalLevel(
            level=3,
            role_required="region_manager",
            min_amount=250001,
            max_amount=1000000,
            description="מנהל מרחב - 250K-1M",
            require_justification=True,
            require_attachments=True,
        ),
        ReleaseApprovalLevel(
            level=4,
            role_required="cfo",
            min_amount=1000001,
            max_amount=float("inf"),
            description='סמנכ"ל כספים - מעל 1M',
            require_justification=True,
            require_attachments=True,
        ),
    ]


def validate_release_amount(
    requested_amount: Decimal,
    budget_total: Decimal,
    budget_utilized: Decimal,
    rules: List[ReleaseRule],
) -> Tuple[bool, Optional[str]]:
    """בדיקת תקינות סכום שחרור"""
    try:
        # בדיקות בסיסיות
        if requested_amount <= 0:
            return False, "סכום השחרור חייב להיות חיובי"

        if requested_amount > budget_total:
            return False, "סכום השחרור גבוה מהתקציב הכולל"

        remaining = budget_total - budget_utilized
        if requested_amount > remaining:
            return False, f"סכום השחרור גבוה מהיתרה הזמינה ({remaining})"

        # בדיקת חוקים
        context = {
            "requested_amount": float(requested_amount),
            "budget_total": float(budget_total),
            "budget_utilized": float(budget_utilized),
            "utilization_rate": float(budget_utilized / budget_total * 100)
            if budget_total > 0
            else 0,
        }

        for rule in rules:
            if rule.is_mandatory:
                is_valid, message = rule.validate(context)
                if not is_valid:
                    return False, message

        return True, None

    except Exception as e:
        logger.error(f"Error validating release amount: {str(e)}")
        return False, f"שגיאה בבדיקת הסכום: {str(e)}"


def calculate_release_amount(
    budget_total: Decimal, calculation_method: str, **kwargs
) -> Decimal:
    """חישוב סכום שחרור"""
    try:
        if calculation_method == ReleaseCalculationMethod.FIXED_AMOUNT.value:
            return Decimal(str(kwargs.get("fixed_amount", 0)))

        elif calculation_method == ReleaseCalculationMethod.PERCENTAGE.value:
            percentage = kwargs.get("percentage", 0)
            return budget_total * Decimal(str(percentage / 100))

        elif calculation_method == ReleaseCalculationMethod.MILESTONE_BASED.value:
            milestone_value = kwargs.get("milestone_value", 0)
            return Decimal(str(milestone_value))

        elif calculation_method == ReleaseCalculationMethod.USAGE_BASED.value:
            usage_factor = kwargs.get("usage_factor", 1.0)
            base_amount = kwargs.get("base_amount", 0)
            return Decimal(str(base_amount * usage_factor))

        else:
            return Decimal("0")

    except Exception as e:
        logger.error(f"Error calculating release amount: {str(e)}")
        return Decimal("0")


def get_release_templates() -> List[ReleaseTemplate]:
    """קבלת תבניות שחרור מוגדרות מראש"""
    return [
        ReleaseTemplate(
            template_id="regular_monthly",
            name="שחרור חודשי רגיל",
            description="שחרור סטנדרטי לתקציב חודשי",
            release_type=ReleaseTypeEnum.REGULAR,
            calculation_method=ReleaseCalculationMethod.PERCENTAGE,
            default_percentage=8.33,  # 1/12 מהתקציב השנתי
            rules=[
                ReleaseRule(
                    rule_type="min_percentage",
                    condition="utilization >= 60%",
                    value=60,
                    description="ניצול מינימלי 60%",
                )
            ],
        ),
        ReleaseTemplate(
            template_id="quarterly_milestone",
            name="שחרור רבעוני לפי אבני דרך",
            description="שחרור המותנה בהשלמת אבני דרך רבעוניות",
            release_type=ReleaseTypeEnum.MILESTONE,
            calculation_method=ReleaseCalculationMethod.MILESTONE_BASED,
            default_percentage=25,
            conditions=[
                ReleaseCondition(
                    condition_type="milestone_completion", required_value=True
                )
            ],
        ),
        ReleaseTemplate(
            template_id="emergency_release",
            name="שחרור חירום",
            description="שחרור מיידי למצבי חירום",
            release_type=ReleaseTypeEnum.EMERGENCY,
            calculation_method=ReleaseCalculationMethod.FIXED_AMOUNT,
            rules=[
                ReleaseRule(
                    rule_type="justification",
                    condition="emergency_justification",
                    value=True,
                    description="נימוק חירום",
                )
            ],
        ),
    ]


def format_release_summary(
    release_type: str,
    amount: Decimal,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """יצירת סיכום שחרור"""
    summary_parts = [
        f"סוג שחרור: {release_type}",
f"סכום: {amount:,.2f}",
        f"סטטוס: {status}",
    ]

    if metadata:
        if "approval_level" in metadata:
            summary_parts.append(f"רמת אישור: {metadata['approval_level']}")
        if "urgency" in metadata:
            summary_parts.append(f"דחיפות: {metadata['urgency']}")

    return " | ".join(summary_parts)


# Export all items
__all__ = [
    "ReleaseTypeEnum",
    "ReleaseStatusEnum",
    "ReleaseFrequencyEnum",
    "ReleaseCalculationMethod",
    "ReleaseRule",
    "ReleaseCondition",
    "ReleaseTemplate",
    "ReleaseApprovalLevel",
    "get_release_rules",
    "get_approval_levels",
    "validate_release_amount",
    "calculate_release_amount",
    "get_release_templates",
    "format_release_summary",
]
