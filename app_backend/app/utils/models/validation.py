# app/utils/models/validation.py
"""
Model validation utilities

Provides functions for validating SQLAlchemy models against database schema
and comparing model structures.
"""

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import MetaData, inspect
from sqlalchemy.orm import Session

from app.core.logging import logger


def validate_model_against_db(
    model_class: Any, table_name: str, db: Session
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validate that a model definition matches the database table structure.

    Args:
        model_class: SQLAlchemy model class
        table_name: Database table name
        db: Database session

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    try:
        # Get database table metadata
        metadata = MetaData()
        metadata.reflect(bind=db.bind, only=[table_name])

        if table_name not in metadata.tables:
            return False, [{"error": f"Table {table_name} not found in database"}]

        db_table = metadata.tables[table_name]
        model_columns = {c.key: c for c in inspect(model_class).mapper.column_attrs}

        # Check for missing columns in model
        for db_col_name, db_col in db_table.columns.items():
            if db_col_name not in model_columns:
                issues.append(
                    {
                        "type": "missing_in_model",
                        "column": db_col_name,
                        "db_type": str(db_col.type),
                        "nullable": db_col.nullable,
                    }
                )

        # Check for columns in model that don't exist in database
        for model_col_name, model_col_attr in model_columns.items():
            model_col = model_col_attr.columns[0]

            if model_col_name not in db_table.columns:
                issues.append(
                    {
                        "type": "missing_in_db",
                        "column": model_col_name,
                        "model_type": str(model_col.type),
                        "nullable": model_col.nullable,
                    }
                )
            else:
                # Column exists, compare properties
                db_col = db_table.columns[model_col_name]

                # Check type compatibility
                if not are_column_types_compatible(db_col.type, model_col.type):
                    issues.append(
                        {
                            "type": "type_mismatch",
                            "column": model_col_name,
                            "db_type": str(db_col.type),
                            "model_type": str(model_col.type),
                        }
                    )

                # Check nullable property
                if db_col.nullable != model_col.nullable:
                    issues.append(
                        {
                            "type": "nullable_mismatch",
                            "column": model_col_name,
                            "db_nullable": db_col.nullable,
                            "model_nullable": model_col.nullable,
                        }
                    )

                # Check primary key
                if db_col.primary_key != model_col.primary_key:
                    issues.append(
                        {
                            "type": "primary_key_mismatch",
                            "column": model_col_name,
                            "db_primary_key": db_col.primary_key,
                            "model_primary_key": model_col.primary_key,
                        }
                    )

        is_valid = len(issues) == 0

        if not is_valid:
            logger.warning(
                f"Model validation failed for {model_class.__name__}: "
                f"{len(issues)} issues found"
            )
        else:
            logger.info(f"Model validation passed for {model_class.__name__}")

        return is_valid, issues

    except Exception as e:
        error_msg = f"Error validating model {model_class.__name__}: {str(e)}"
        logger.error(error_msg)
        return False, [{"error": error_msg}]


def compare_models(
    model_a: Any, model_b: Any, ignore_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Compare the structure of two model classes.

    Args:
        model_a: First model class
        model_b: Second model class
        ignore_fields: List of fields to exclude from comparison

    Returns:
        List of differences found
    """
    if ignore_fields is None:
        ignore_fields = []

    differences = []

    # Get columns for both models
    columns_a = {c.key: c for c in inspect(model_a).mapper.column_attrs}
    columns_b = {c.key: c for c in inspect(model_b).mapper.column_attrs}

    # Get column names excluding ignored fields
    names_a = set(columns_a.keys()) - set(ignore_fields)
    names_b = set(columns_b.keys()) - set(ignore_fields)

    # Find missing columns
    for col_name in names_a - names_b:
        col = columns_a[col_name].columns[0]
        differences.append(
            {
                "type": "missing_column",
                "model": model_b.__name__,
                "column": col_name,
                "details": {"type": str(col.type), "nullable": col.nullable},
            }
        )

    for col_name in names_b - names_a:
        col = columns_b[col_name].columns[0]
        differences.append(
            {
                "type": "missing_column",
                "model": model_a.__name__,
                "column": col_name,
                "details": {"type": str(col.type), "nullable": col.nullable},
            }
        )

    # Compare common columns
    for col_name in names_a.intersection(names_b):
        col_a = columns_a[col_name].columns[0]
        col_b = columns_b[col_name].columns[0]

        # Compare types
        if str(col_a.type) != str(col_b.type):
            differences.append(
                {
                    "type": "type_mismatch",
                    "column": col_name,
                    "model_a_type": str(col_a.type),
                    "model_b_type": str(col_b.type),
                }
            )

        # Compare nullable
        if col_a.nullable != col_b.nullable:
            differences.append(
                {
                    "type": "nullable_mismatch",
                    "column": col_name,
                    "model_a_nullable": col_a.nullable,
                    "model_b_nullable": col_b.nullable,
                }
            )

        # Compare primary key
        if col_a.primary_key != col_b.primary_key:
            differences.append(
                {
                    "type": "primary_key_mismatch",
                    "column": col_name,
                    "model_a_pk": col_a.primary_key,
                    "model_b_pk": col_b.primary_key,
                }
            )

    return differences


def find_instance_discrepancies(
    instance_a: Any, instance_b: Any, exclude_fields: Optional[List[str]] = None
) -> Dict[str, List[Any]]:
    """
    Find differences between two model instances.

    Args:
        instance_a: First model instance
        instance_b: Second model instance
        exclude_fields: Fields to exclude from comparison

    Returns:
        Dictionary with discrepancies by field
    """
    if exclude_fields is None:
        exclude_fields = []

    discrepancies = {}

    # Get all attributes from both instances
    attrs_a = {
        c.key: getattr(instance_a, c.key, None)
        for c in inspect(instance_a.__class__).mapper.column_attrs
    }
    attrs_b = {
        c.key: getattr(instance_b, c.key, None)
        for c in inspect(instance_b.__class__).mapper.column_attrs
    }

    # Compare all fields
    all_fields = set(attrs_a.keys()).union(set(attrs_b.keys())) - set(exclude_fields)

    for field in all_fields:
        value_a = attrs_a.get(field)
        value_b = attrs_b.get(field)

        if field not in attrs_a:
            discrepancies[field] = ["missing_in_a", None, value_b]
        elif field not in attrs_b:
            discrepancies[field] = ["missing_in_b", value_a, None]
        elif value_a != value_b:
            discrepancies[field] = ["value_mismatch", value_a, value_b]

    return discrepancies


def are_column_types_compatible(db_type: Any, model_type: Any) -> bool:
    """
    Check if database and model column types are compatible.

    Args:
        db_type: Database column type
        model_type: Model column type

    Returns:
        True if types are compatible
    """
    db_type_str = str(db_type).lower()
    model_type_str = str(model_type).lower()

    # Direct match
    if db_type_str == model_type_str:
        return True

    # Common compatibility patterns
    compatibility_patterns = [
        ("int", "int"),
        ("char", "char"),
        ("varchar", "string"),
        ("nvarchar", "string"),
        ("text", "string"),
        ("text", "text"),
        ("datetime", "datetime"),
        ("timestamp", "datetime"),
        ("bool", "boolean"),
        ("bit", "boolean"),
        ("float", "float"),
        ("real", "float"),
        ("double", "float"),
        ("decimal", "decimal"),
        ("numeric", "decimal"),
        ("uuid", "uuid"),
        ("uniqueidentifier", "uuid"),
    ]

    for db_pattern, model_pattern in compatibility_patterns:
        if db_pattern in db_type_str and model_pattern in model_type_str:
            return True

    return False
