"""Routers module."""
from fastapi import APIRouter
import logging
import os
import importlib

logger = logging.getLogger(__name__)

# Create main API router
api_router = APIRouter()

# API Metadata
API_METADATA = {
    "title": "Forest Management System API",
    "version": "1.0.0",
    "description": "ניהול יערות ופרויקטים",
}

# List of router modules to load
ROUTER_MODULES = [
    "auth",
    "users",
    "roles",
    "permissions",
    "role_assignments",
    "regions",
    "areas",
    "locations",
    "departments",
    "projects",
    "project_assignments",
    "budgets",
    "budget_transfers",
    "worklogs",
    "reports",
    "dashboard",
    "websocket",
    "admin",
    "admin_projects",
    "activity_logs",
    "support_tickets",
    "work_orders",
    "equipment",
    "supplier_constraint_reasons",
    "supplier_rotations",
    "equipment_categories",
    "invoices",
    "suppliers",
    "notifications",
    "activity_types",
    "equipment_types",
    "system_rates",
    "pricing",
    "pdf_preview",
    "supplier_portal",
    "geo",
    "settings",
    "equipment_rates",
    # "supplier_distribution",  # removed — file deleted, not in use
]

# Load routers dynamically
loaded_routers = []
failed_routers = []

for module_name in ROUTER_MODULES:
    try:
        module = importlib.import_module(f"app.routers.{module_name}")
        if hasattr(module, 'router'):
            api_router.include_router(
                module.router,
                tags=[module_name.replace("_", " ").title()]
            )
            loaded_routers.append(module_name)
            logger.info(f"[OK] Loaded router: {module_name}")  # תיקון: הסרת אמוג'י
    except Exception as e:
        failed_routers.append(module_name)
        logger.warning(f"[FAILED] Failed to load router {module_name}: {str(e)[:100]}")  # תיקון: הסרת אמוג'י

logger.info(f"Loaded {len(loaded_routers)}/{len(ROUTER_MODULES)} routers")
if failed_routers:
    logger.warning(f"Failed routers: {', '.join(failed_routers)}")

__all__ = ["api_router", "API_METADATA"]
