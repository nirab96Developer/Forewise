# app/utils/models/conversion.py
"""
Model conversion and migration utilities

Provides functions for converting data between models and performing
batch migrations.
"""

import time
import uuid
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.logging import logger


def model_to_dict(
    model: Any,
    include_relationships: bool = False,
    exclude_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convert a model instance to dictionary.

    Args:
        model: SQLAlchemy model instance or Pydantic model
        include_relationships: Whether to include relationship fields
        exclude_fields: Fields to exclude

    Returns:
        Dictionary representation
    """
    if exclude_fields is None:
        exclude_fields = []

    # Handle Pydantic models
    if isinstance(model, BaseModel):
        return {k: v for k, v in model.model_dump().items() if k not in exclude_fields}

    # Handle SQLAlchemy models
    result = {}

    # Get column attributes
    for column in inspect(model).mapper.column_attrs:
        if column.key not in exclude_fields:
            result[column.key] = getattr(model, column.key)

    # Include relationships if requested
    if include_relationships:
        for relationship in inspect(model).mapper.relationships:
            if relationship.key not in exclude_fields:
                related_value = getattr(model, relationship.key)

                if related_value is not None:
                    if hasattr(related_value, "__iter__") and not isinstance(
                        related_value, (str, bytes)
                    ):
                        # Collection of related objects
                        result[relationship.key] = [
                            model_to_dict(item, False, exclude_fields)
                            for item in related_value
                        ]
                    else:
                        # Single related object
                        result[relationship.key] = model_to_dict(
                            related_value, False, exclude_fields
                        )
                else:
                    result[relationship.key] = None

    return result


def dict_to_model(
    model_class: Any, data: Dict[str, Any], ignore_extra: bool = True
) -> Any:
    """
    Convert dictionary to model instance.

    Args:
        model_class: Model class (SQLAlchemy or Pydantic)
        data: Dictionary of data
        ignore_extra: Whether to ignore extra fields

    Returns:
        Model instance
    """
    # Handle Pydantic models
    if issubclass(model_class, BaseModel):
        if ignore_extra:
            # Filter to valid fields only
            model_fields = model_class.model_fields.keys()
            filtered_data = {k: v for k, v in data.items() if k in model_fields}
            return model_class(**filtered_data)
        else:
            return model_class(**data)

    # Handle SQLAlchemy models
    instance = model_class()

    # Get valid column names
    valid_columns = {c.key for c in inspect(model_class).mapper.column_attrs}

    for key, value in data.items():
        if ignore_extra and key not in valid_columns:
            continue

        if hasattr(instance, key):
            setattr(instance, key, value)

    return instance


def convert_data_between_models(
    source_data: Union[Any, Dict[str, Any]],
    target_model: Any,
    field_mapping: Optional[Dict[str, str]] = None,
    value_converters: Optional[Dict[str, Callable]] = None,
    exclude_fields: Optional[List[str]] = None,
) -> Any:
    """
    Convert data from one model format to another.

    Args:
        source_data: Source model instance or dictionary
        target_model: Target model class
        field_mapping: Map source fields to target fields
        value_converters: Custom conversion functions by field
        exclude_fields: Fields to exclude

    Returns:
        Instance of target model
    """
    if field_mapping is None:
        field_mapping = {}
    if value_converters is None:
        value_converters = {}
    if exclude_fields is None:
        exclude_fields = []

    # Convert source to dictionary
    if isinstance(source_data, dict):
        source_dict = source_data.copy()
    else:
        source_dict = model_to_dict(source_data)

    # Apply field mappings
    target_dict = {}
    for source_field, value in source_dict.items():
        if source_field in exclude_fields:
            continue

        # Get target field name
        target_field = field_mapping.get(source_field, source_field)

        # Apply value converter if exists
        if source_field in value_converters:
            value = value_converters[source_field](value)

        target_dict[target_field] = value

    # Create target model instance
    return dict_to_model(target_model, target_dict)


async def migrate_data_batch(
    db: Session,
    source_model: Any,
    target_model: Any,
    batch_size: int = 100,
    filter_criteria: Optional[Dict[str, Any]] = None,
    field_mapping: Optional[Dict[str, str]] = None,
    value_converters: Optional[Dict[str, Callable]] = None,
    on_error: str = "skip",  # "skip", "raise", "rollback"
) -> Dict[str, Any]:
    """
    Migrate data between models in batches.

    Args:
        db: Database session
        source_model: Source model class
        target_model: Target model class
        batch_size: Records per batch
        filter_criteria: Filter for source records
        field_mapping: Field name mappings
        value_converters: Value conversion functions
        on_error: Error handling strategy

    Returns:
        Migration statistics
    """
    start_time = time.time()
    stats = {
        "total": 0,
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
    }

    try:
        # Build source query
        query = db.query(source_model)
        if filter_criteria:
            for field, value in filter_criteria.items():
                query = query.filter(getattr(source_model, field) == value)

        # Get total count
        stats["total"] = query.count()
        logger.info(f"Starting migration of {stats['total']} records")

        # Process in batches
        offset = 0
        while True:
            batch = query.limit(batch_size).offset(offset).all()
            if not batch:
                break

            batch_start = time.time()
            batch_successful = 0

            for source_instance in batch:
                stats["processed"] += 1

                try:
                    # Convert to target model
                    target_instance = convert_data_between_models(
                        source_instance, target_model, field_mapping, value_converters
                    )

                    # Check if already exists (by primary key)
                    pk_name = get_primary_key_name(target_model)
                    if pk_name:
                        pk_value = getattr(target_instance, pk_name)
                        existing = (
                            db.query(target_model)
                            .filter(getattr(target_model, pk_name) == pk_value)
                            .first()
                        )

                        if existing:
                            # Update existing
                            for key, value in model_to_dict(target_instance).items():
                                if key != pk_name:
                                    setattr(existing, key, value)
                        else:
                            # Add new
                            db.add(target_instance)
                    else:
                        # No primary key, always add new
                        db.add(target_instance)

                    stats["successful"] += 1
                    batch_successful += 1

                except Exception as e:
                    stats["failed"] += 1
                    error_info = {
                        "source_id": getattr(
                            source_instance, get_primary_key_name(source_model), None
                        ),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                    stats["errors"].append(error_info)

                    if on_error == "raise":
                        raise
                    elif on_error == "rollback":
                        db.rollback()
                        raise
                    # else: skip and continue

            # Commit batch
            try:
                db.commit()
                batch_duration = time.time() - batch_start
                logger.info(
                    f"Batch completed: {batch_successful} records in {batch_duration:.2f}s "
                    f"({batch_successful/batch_duration:.1f} records/s)"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"Batch commit failed: {str(e)}")
                if on_error != "skip":
                    raise

            offset += batch_size

            # Progress update every 10 batches
            if offset % (batch_size * 10) == 0:
                progress = (
                    (stats["processed"] / stats["total"] * 100)
                    if stats["total"] > 0
                    else 0
                )
                logger.info(
                    f"Migration progress: {progress:.1f}% ({stats['processed']}/{stats['total']})"
                )

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        if on_error == "raise":
            raise

    # Calculate final statistics
    duration = time.time() - start_time
    stats["duration_seconds"] = duration
    stats["records_per_second"] = stats["processed"] / duration if duration > 0 else 0
    stats["success_rate"] = (
        (stats["successful"] / stats["total"] * 100) if stats["total"] > 0 else 0
    )

    logger.info(
        f"Migration completed: {stats['successful']}/{stats['total']} records "
        f"in {duration:.1f}s ({stats['success_rate']:.1f}% success rate)"
    )

    return stats


def type_safe_convert(value: Any, target_type: Union[type, str]) -> Any:
    """
    Safely convert value to target type.

    Args:
        value: Value to convert
        target_type: Target type or type name

    Returns:
        Converted value
    """
    if value is None:
        return None

    # Handle string type names
    if isinstance(target_type, str):
        type_map = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "datetime": datetime,
            "date": date,
            "uuid": uuid.UUID,
            "dict": dict,
            "list": list,
        }
        target_type = type_map.get(target_type.lower(), str)

    try:
        # Special conversions
        if target_type == bool and isinstance(value, str):
            return value.lower() in ("true", "yes", "1", "y", "t")

        elif target_type == datetime:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            elif isinstance(value, date):
                return datetime.combine(value, datetime.min.time())

        elif target_type == date:
            if isinstance(value, str):
                return date.fromisoformat(value)
            elif isinstance(value, datetime):
                return value.date()

        elif target_type == uuid.UUID:
            if isinstance(value, str):
                return uuid.UUID(value)

        # Default conversion
        return target_type(value)

    except Exception as e:
        logger.warning(
            f"Type conversion failed: {value} to {target_type.__name__}: {str(e)}"
        )
        return value


def get_primary_key_name(model_class: Any) -> Optional[str]:
    """Get primary key column name for a model."""
    for column in inspect(model_class).mapper.column_attrs:
        if column.columns[0].primary_key:
            return column.key
    return None
