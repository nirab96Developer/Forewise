-- ============================================================================
-- Migration 01: ADD UNIQUE Constraints על מפתחות עסקיים
-- תאריך: 2026-01-10
-- ============================================================================
-- קריטי! חייב לרוץ לפני שאר ה-migrations
-- ============================================================================

USE [KKLForest];
GO

PRINT '========================================';
PRINT 'Migration 01: Adding UNIQUE Constraints';
PRINT '========================================';
PRINT '';

-- Check for duplicates BEFORE adding constraints
PRINT 'Step 1: Checking for duplicates...';
PRINT '';

DECLARE @hasDuplicates BIT = 0;

-- roles.code
IF EXISTS (
    SELECT code, COUNT(*) 
    FROM dbo.roles 
    WHERE code IS NOT NULL
    GROUP BY code 
    HAVING COUNT(*) > 1
)
BEGIN
    PRINT '⚠️  WARNING: Duplicates found in roles.code!';
    SELECT code, COUNT(*) as count
    FROM dbo.roles
    GROUP BY code
    HAVING COUNT(*) > 1;
    SET @hasDuplicates = 1;
END

-- permissions.code
IF EXISTS (
    SELECT code, COUNT(*) 
    FROM dbo.permissions 
    WHERE code IS NOT NULL
    GROUP BY code 
    HAVING COUNT(*) > 1
)
BEGIN
    PRINT '⚠️  WARNING: Duplicates found in permissions.code!';
    SELECT code, COUNT(*) as count
    FROM dbo.permissions
    GROUP BY code
    HAVING COUNT(*) > 1;
    SET @hasDuplicates = 1;
END

-- users.email
IF EXISTS (
    SELECT email, COUNT(*) 
    FROM dbo.users 
    WHERE email IS NOT NULL
    GROUP BY email 
    HAVING COUNT(*) > 1
)
BEGIN
    PRINT '⚠️  WARNING: Duplicates found in users.email!';
    SELECT email, COUNT(*) as count
    FROM dbo.users
    GROUP BY email
    HAVING COUNT(*) > 1;
    SET @hasDuplicates = 1;
END

-- users.username (NULL allowed, so check only non-NULL)
IF EXISTS (
    SELECT username, COUNT(*) 
    FROM dbo.users 
    WHERE username IS NOT NULL
    GROUP BY username 
    HAVING COUNT(*) > 1
)
BEGIN
    PRINT '⚠️  WARNING: Duplicates found in users.username!';
    SELECT username, COUNT(*) as count
    FROM dbo.users
    WHERE username IS NOT NULL
    GROUP BY username
    HAVING COUNT(*) > 1;
    SET @hasDuplicates = 1;
END

IF @hasDuplicates = 1
BEGIN
    PRINT '';
    PRINT '❌ ERROR: Cannot proceed - duplicates must be resolved first!';
    PRINT 'Please fix duplicates manually and re-run this script.';
    RAISERROR('Duplicates found - migration aborted', 16, 1);
    RETURN;
END

PRINT '✅ No duplicates found - proceeding with UNIQUE constraints...';
PRINT '';

-- ============================================================================
-- Step 2: Add UNIQUE Constraints
-- ============================================================================

BEGIN TRANSACTION;

BEGIN TRY

    -- 1. roles.code
    PRINT 'Adding UNIQUE: roles.code...';
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.roles') AND name = 'UQ_roles_code')
    BEGIN
        ALTER TABLE dbo.roles
            ADD CONSTRAINT UQ_roles_code UNIQUE (code);
        PRINT '  ✅ Added UQ_roles_code';
    END
    ELSE
        PRINT '  ℹ️  UQ_roles_code already exists';

    -- 2. permissions.code
    PRINT 'Adding UNIQUE: permissions.code...';
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.permissions') AND name = 'UQ_permissions_code')
    BEGIN
        ALTER TABLE dbo.permissions
            ADD CONSTRAINT UQ_permissions_code UNIQUE (code);
        PRINT '  ✅ Added UQ_permissions_code';
    END
    ELSE
        PRINT '  ℹ️  UQ_permissions_code already exists';

    -- 3. users.email
    PRINT 'Adding UNIQUE: users.email...';
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.users') AND name = 'UQ_users_email')
    BEGIN
        ALTER TABLE dbo.users
            ADD CONSTRAINT UQ_users_email UNIQUE (email);
        PRINT '  ✅ Added UQ_users_email';
    END
    ELSE
        PRINT '  ℹ️  UQ_users_email already exists';

    -- 4. users.username (nullable, but unique when present)
    PRINT 'Adding UNIQUE: users.username...';
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.users') AND name = 'UQ_users_username')
    BEGIN
        CREATE UNIQUE NONCLUSTERED INDEX UQ_users_username
            ON dbo.users(username)
            WHERE username IS NOT NULL;
        PRINT '  ✅ Added UQ_users_username (filtered)';
    END
    ELSE
        PRINT '  ℹ️  UQ_users_username already exists';

    -- 5. regions.code (if column exists)
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'regions' AND COLUMN_NAME = 'code')
    BEGIN
        PRINT 'Adding UNIQUE: regions.code...';
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.regions') AND name = 'UQ_regions_code')
        BEGIN
            ALTER TABLE dbo.regions
                ADD CONSTRAINT UQ_regions_code UNIQUE (code);
            PRINT '  ✅ Added UQ_regions_code';
        END
        ELSE
            PRINT '  ℹ️  UQ_regions_code already exists';
    END
    ELSE
        PRINT '  ℹ️  regions.code column does not exist - skipping';

    -- 6. areas.code (if column exists)
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'areas' AND COLUMN_NAME = 'code')
    BEGIN
        PRINT 'Adding UNIQUE: areas.code...';
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.areas') AND name = 'UQ_areas_code')
        BEGIN
            ALTER TABLE dbo.areas
                ADD CONSTRAINT UQ_areas_code UNIQUE (code);
            PRINT '  ✅ Added UQ_areas_code';
        END
        ELSE
            PRINT '  ℹ️  UQ_areas_code already exists';
    END
    ELSE
        PRINT '  ℹ️  areas.code column does not exist - skipping';

    -- 7. projects.code (if column exists)
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'projects' AND COLUMN_NAME = 'code')
    BEGIN
        PRINT 'Adding UNIQUE: projects.code...';
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.projects') AND name = 'UQ_projects_code')
        BEGIN
            ALTER TABLE dbo.projects
                ADD CONSTRAINT UQ_projects_code UNIQUE (code);
            PRINT '  ✅ Added UQ_projects_code';
        END
        ELSE
            PRINT '  ℹ️  UQ_projects_code already exists';
    END
    ELSE
        PRINT '  ℹ️  projects.code column does not exist - skipping';

    -- 8. suppliers.code (if column exists)
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'suppliers' AND COLUMN_NAME = 'code')
    BEGIN
        PRINT 'Adding UNIQUE: suppliers.code...';
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.suppliers') AND name = 'UQ_suppliers_code')
        BEGIN
            ALTER TABLE dbo.suppliers
                ADD CONSTRAINT UQ_suppliers_code UNIQUE (code);
            PRINT '  ✅ Added UQ_suppliers_code';
        END
        ELSE
            PRINT '  ℹ️  UQ_suppliers_code already exists';
    END
    ELSE
        PRINT '  ℹ️  suppliers.code column does not exist - skipping';

    -- 9. equipment_categories.code
    PRINT 'Adding UNIQUE: equipment_categories.code...';
    IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.equipment_categories') AND name = 'UQ_equipment_categories_code')
    BEGIN
        ALTER TABLE dbo.equipment_categories
            ADD CONSTRAINT UQ_equipment_categories_code UNIQUE (code);
        PRINT '  ✅ Added UQ_equipment_categories_code';
    END
    ELSE
        PRINT '  ℹ️  UQ_equipment_categories_code already exists';

    COMMIT TRANSACTION;
    
    PRINT '';
    PRINT '✅ Migration 01 completed successfully!';
    PRINT '';

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    
    PRINT '';
    PRINT '❌ Migration 01 failed!';
    PRINT 'Error: ' + ERROR_MESSAGE();
    PRINT '';
    
    THROW;
END CATCH

GO

