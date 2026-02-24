# app/utils/models/schema.py
"""
Model schema utilities

Provides functions for extracting and analyzing model schemas.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import inspect
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import Session

from app.core.logging import logger


def get_model_schema(model_class: Any) -> Dict[str, Any]:
    """
    Extract complete schema information from a model class.

    Args:
        model_class: SQLAlchemy model class

    Returns:
        Dictionary with model schema
    """
    try:
        inspector = inspect(model_class)

        schema = {
            "name": model_class.__name__,
            "table_name": getattr(model_class, "__tablename__", ""),
            "columns": {},
            "relationships": {},
            "indexes": [],
            "constraints": [],
            "primary_keys": [],
        }

        # Extract columns
        for column_attr in inspector.column_attrs:
            column = column_attr.columns[0]

            column_info = {
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "foreign_key": bool(column.foreign_keys),
                "unique": column.unique or False,
                "index": column.index or False,
                "default": str(column.default) if column.default else None,
                "autoincrement": getattr(column, "autoincrement", False),
            }

            # Add foreign key details
            if column.foreign_keys:
                fk_info = []
                for fk in column.foreign_keys:
                    fk_info.append(
                        {
                            "table": fk.column.table.name,
                            "column": fk.column.name,
                            "ondelete": fk.ondelete,
                            "onupdate": fk.onupdate,
                        }
                    )
                column_info["foreign_key_info"] = fk_info

            schema["columns"][column_attr.key] = column_info

            if column.primary_key:
                schema["primary_keys"].append(column_attr.key)

        # Extract relationships
        for rel in inspector.relationships:
            rel_info = {
                "target": rel.target.name
                if hasattr(rel.target, "name")
                else str(rel.target),
                "type": "one_to_many" if rel.uselist else "many_to_one",
                "back_populates": rel.back_populates,
                "cascade": rel.cascade if hasattr(rel, "cascade") else None,
                "lazy": rel.lazy if hasattr(rel, "lazy") else None,
            }
            schema["relationships"][rel.key] = rel_info

        # Extract indexes if available
        if hasattr(model_class.__table__, "indexes"):
            for index in model_class.__table__.indexes:
                index_info = {
                    "name": index.name,
                    "columns": [col.name for col in index.columns],
                    "unique": index.unique,
                }
                schema["indexes"].append(index_info)

        # Extract constraints if available
        if hasattr(model_class.__table__, "constraints"):
            for constraint in model_class.__table__.constraints:
                constraint_info = {
                    "name": constraint.name,
                    "type": type(constraint).__name__,
                }
                schema["constraints"].append(constraint_info)

        return schema

    except Exception as e:
        logger.error(f"Error extracting schema for {model_class.__name__}: {str(e)}")
        return {"error": str(e)}


def get_all_models_schema(models: List[Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get schema for multiple models.

    Args:
        models: List of model classes

    Returns:
        Dictionary mapping model names to schemas
    """
    schemas = {}

    for model in models:
        try:
            schema = get_model_schema(model)
            schemas[model.__name__] = schema
        except Exception as e:
            logger.error(f"Failed to get schema for {model.__name__}: {str(e)}")
            schemas[model.__name__] = {"error": str(e)}

    return schemas


def analyze_model_relationships(model_class: Any) -> Dict[str, Any]:
    """
    Analyze relationships for a model.

    Args:
        model_class: SQLAlchemy model class

    Returns:
        Detailed relationship analysis
    """
    try:
        inspector = inspect(model_class)

        analysis = {
            "model": model_class.__name__,
            "relationships": {},
            "dependency_graph": {"depends_on": [], "depended_by": []},
        }

        for rel in inspector.relationships:
            target_model = rel.mapper.class_

            rel_detail = {
                "target_model": target_model.__name__,
                "target_table": target_model.__tablename__,
                "relationship_type": "one_to_many" if rel.uselist else "many_to_one",
                "foreign_keys": [],
            }

            # Find foreign key columns
            for fk in rel._calculated_foreign_keys:
                if hasattr(fk, "parent"):
                    rel_detail["foreign_keys"].append(
                        {
                            "local_column": fk.parent.name,
                            "remote_column": fk.column.name,
                        }
                    )

            analysis["relationships"][rel.key] = rel_detail

            # Build dependency graph
            if rel.uselist:
                # One-to-many: this model is depended on by target
                analysis["dependency_graph"]["depended_by"].append(
                    target_model.__name__
                )
            else:
                # Many-to-one: this model depends on target
                analysis["dependency_graph"]["depends_on"].append(target_model.__name__)

        return analysis

    except Exception as e:
        logger.error(
            f"Error analyzing relationships for {model_class.__name__}: {str(e)}"
        )
        return {"error": str(e)}


def get_table_stats(db: Session, model_class: Any) -> Dict[str, Any]:
    """
    Get statistics for a model's table.

    Args:
        db: Database session
        model_class: Model class

    Returns:
        Table statistics
    """
    try:
        table_name = model_class.__tablename__

        # Get row count
        row_count = db.query(model_class).count()

        # Get table size (this is database-specific)
        # Example for PostgreSQL:
        size_query = f"""
        SELECT 
            pg_size_pretty(pg_total_relation_size('{table_name}')) as total_size,
            pg_size_pretty(pg_relation_size('{table_name}')) as table_size,
            pg_size_pretty(pg_indexes_size('{table_name}')) as indexes_size
        """

        try:
            result = db.execute(size_query).first()
            size_info = {
                "total_size": result.total_size if result else "N/A",
                "table_size": result.table_size if result else "N/A",
                "indexes_size": result.indexes_size if result else "N/A",
            }
        except:
            size_info = {"note": "Size information not available for this database"}

        return {
            "table_name": table_name,
            "row_count": row_count,
            "size_info": size_info,
            "column_count": len(list(inspect(model_class).column_attrs)),
            "relationship_count": len(list(inspect(model_class).relationships)),
            "index_count": len(model_class.__table__.indexes)
            if hasattr(model_class.__table__, "indexes")
            else 0,
        }

    except Exception as e:
        logger.error(f"Error getting table stats for {model_class.__name__}: {str(e)}")
        return {"error": str(e)}
