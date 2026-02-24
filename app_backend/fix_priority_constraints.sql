-- Fix Priority Enum Constraints in SQL Server
-- Add CHECK constraint and DEFAULT value for priority column

-- First, check if constraint already exists
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CK_projects_priority')
BEGIN
    -- Add CHECK constraint for priority values
    ALTER TABLE dbo.projects 
    ADD CONSTRAINT CK_projects_priority
    CHECK (priority IN ('low','normal','medium','high','urgent'));
    
    PRINT 'Added CHECK constraint CK_projects_priority';
END
ELSE
BEGIN
    PRINT 'CHECK constraint CK_projects_priority already exists';
END

-- Add DEFAULT value for priority column
IF NOT EXISTS (SELECT * FROM sys.default_constraints WHERE name = 'DF_projects_priority')
BEGIN
    ALTER TABLE dbo.projects 
    ADD CONSTRAINT DF_projects_priority
    DEFAULT ('normal') FOR priority;
    
    PRINT 'Added DEFAULT constraint DF_projects_priority';
END
ELSE
BEGIN
    PRINT 'DEFAULT constraint DF_projects_priority already exists';
END

-- Update any NULL priority values to 'normal'
UPDATE dbo.projects 
SET priority = 'normal' 
WHERE priority IS NULL;

PRINT 'Updated NULL priority values to normal';

-- Verify the changes
SELECT 
    priority,
    COUNT(*) as count
FROM dbo.projects 
GROUP BY priority
ORDER BY priority;

PRINT 'Priority distribution after fix:';

