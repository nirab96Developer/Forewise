# app/utils/models/__init__.py
"""
Model utilities package
"""

from app.utils.models.conversion import (convert_data_between_models,
                                         dict_to_model, get_primary_key_name,
                                         migrate_data_batch, model_to_dict,
                                         type_safe_convert)
from app.utils.models.schema import (analyze_model_relationships,
                                     get_all_models_schema, get_model_schema,
                                     get_table_stats)
from app.utils.models.validation import (are_column_types_compatible,
                                         compare_models,
                                         find_instance_discrepancies,
                                         validate_model_against_db)

__all__ = [
    # Validation
    "validate_model_against_db",
    "compare_models",
    "find_instance_discrepancies",
    "are_column_types_compatible",
    # Conversion
    "model_to_dict",
    "dict_to_model",
    "convert_data_between_models",
    "migrate_data_batch",
    "type_safe_convert",
    "get_primary_key_name",
    # Schema
    "get_model_schema",
    "get_all_models_schema",
    "analyze_model_relationships",
    "get_table_stats",
]
