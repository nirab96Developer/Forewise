#!/usr/bin/env python3
"""
Run Work Orders Index Creation Script
Executes the optimized index creation for work_orders table
"""

import os
import sys

# Add backend to path
sys.path.insert(0, '/root/kkl-forest/app_backend')

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv('/root/kkl-forest/app_backend/.env')

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

print("=" * 60)
print("   WORK ORDERS INDEX CREATION")
print("=" * 60)
print()

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# SQL commands to run (split into individual statements)
sql_commands = [
    # Check existing indexes first
    """
    SELECT 
        i.name AS index_name,
        i.type_desc
    FROM sys.indexes i
    WHERE i.object_id = OBJECT_ID('dbo.work_orders')
      AND i.name IS NOT NULL
    ORDER BY i.name
    """,
    
    # Index 1: Default list query
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_list_default' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_list_default
        ON dbo.work_orders (deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, priority, 
            project_id, supplier_id, equipment_id, location_id,
            work_start_date, work_end_date, is_active
        )
    END
    """,
    
    # Index 2: Status filter
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_status_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_status_list
        ON dbo.work_orders (status, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, priority, 
            project_id, supplier_id, is_active
        )
    END
    """,
    
    # Index 3: Project filter
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_project_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_project_list
        ON dbo.work_orders (project_id, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, priority, 
            supplier_id, is_active, work_start_date
        )
    END
    """,
    
    # Index 4: Supplier filter (with WHERE clause - filtered index)
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_supplier_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_supplier_list
        ON dbo.work_orders (supplier_id, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, priority, project_id
        )
        WHERE supplier_id IS NOT NULL
    END
    """,
    
    # Index 5: Count optimization
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_count' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_count
        ON dbo.work_orders (deleted_at, status, project_id)
        INCLUDE (id)
    END
    """,
    
    # Index 6: Priority filter
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_priority_list' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_priority_list
        ON dbo.work_orders (priority, deleted_at, created_at DESC)
        INCLUDE (
            id, order_number, title, status, project_id
        )
    END
    """,
    
    # Index 7: Date range filter
    """
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_work_orders_date_range' AND object_id = OBJECT_ID('dbo.work_orders'))
    BEGIN
        CREATE NONCLUSTERED INDEX IX_work_orders_date_range
        ON dbo.work_orders (work_start_date, deleted_at)
        INCLUDE (
            id, order_number, status, project_id, priority
        )
    END
    """,
    
    # Update statistics
    """
    UPDATE STATISTICS dbo.work_orders WITH FULLSCAN
    """,
    
    # Show final indexes
    """
    SELECT 
        i.name AS index_name,
        i.type_desc,
        i.is_unique
    FROM sys.indexes i
    WHERE i.object_id = OBJECT_ID('dbo.work_orders')
      AND i.name IS NOT NULL
    ORDER BY i.name
    """
]

index_names = [
    "Check existing indexes",
    "IX_work_orders_list_default (main query)",
    "IX_work_orders_status_list (status filter)",
    "IX_work_orders_project_list (project filter)",
    "IX_work_orders_supplier_list (supplier filter)",
    "IX_work_orders_count (count optimization)",
    "IX_work_orders_priority_list (priority filter)",
    "IX_work_orders_date_range (date range)",
    "Update statistics",
    "Show final indexes"
]

with engine.connect() as conn:
    for i, (sql, name) in enumerate(zip(sql_commands, index_names)):
        print(f"[{i+1}/{len(sql_commands)}] {name}...")
        try:
            result = conn.execute(text(sql))
            
            # If it's a SELECT, show results
            if sql.strip().upper().startswith('SELECT') or 'SELECT' in sql[:50].upper():
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(f"    → {row}")
                else:
                    print("    (no results)")
            else:
                conn.commit()
                print("    ✓ Done")
        except Exception as e:
            print(f"    ❌ Error: {e}")
            # Continue with next command
    
    # Performance test
    print()
    print("=" * 60)
    print("   PERFORMANCE TEST")
    print("=" * 60)
    print()
    
    import time
    
    test_sql = """
    SELECT TOP 50
        wo.id, wo.order_number, wo.title, wo.status, wo.priority,
        wo.created_at, wo.project_id, wo.supplier_id
    FROM dbo.work_orders wo
    WHERE wo.deleted_at IS NULL
    ORDER BY wo.created_at DESC
    """
    
    print("Running: SELECT TOP 50 ... ORDER BY created_at DESC")
    start = time.time()
    result = conn.execute(text(test_sql))
    rows = result.fetchall()
    elapsed = time.time() - start
    
    print(f"✓ Returned {len(rows)} rows in {elapsed:.3f} seconds")
    
    if elapsed < 1:
        print("🎉 SUCCESS: Query is now fast!")
    elif elapsed < 5:
        print("⚠️ IMPROVED: Query is faster but could be better")
    else:
        print("❌ STILL SLOW: May need additional optimization")

print()
print("=" * 60)
print("   COMPLETE")
print("=" * 60)

