# =========================================================================
# סקריפט אוטומציה למיגרציה - קק"ל (PowerShell)
# =========================================================================
# שימוש: .\run_migration.ps1 -Step <step>
#
# Steps:
#   Backup    - גיבוי הבסיס
#   Check     - בדיקת איכות נתונים
#   Perms     - מיגרציית הרשאות
#   Suppliers - מיגרציית ספקים
#   Python    - עדכון קוד Python
#   All       - הכל ברצף (זהירות!)
# =========================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Backup", "Check", "Perms", "Suppliers", "Python", "All", "Help")]
    [string]$Step = "Help",
    
    [Parameter(Mandatory=$false)]
    [string]$DbServer = "localhost",
    
    [Parameter(Mandatory=$false)]
    [string]$DbName = "kkl_forest",
    
    [Parameter(Mandatory=$false)]
    [string]$DbUser = "",
    
    [Parameter(Mandatory=$false)]
    [string]$BackupDir = ".\backups",
    
    [Parameter(Mandatory=$false)]
    [string]$MigrationsDir = ".\app_backend\database\migrations"
)

# Functions
function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host $Message -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green
    Write-Host ""
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "❌ ERROR: $Message" -ForegroundColor Red
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "⚠️  WARNING: $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

# Check if sqlcmd is available
function Test-SqlCmd {
    if (-not (Get-Command sqlcmd -ErrorAction SilentlyContinue)) {
        Write-Error-Message "sqlcmd not found! Please install SQL Server command-line tools."
        exit 1
    }
}

# Build sqlcmd auth params
function Get-SqlCmdAuth {
    if ($DbUser) {
        return "-U $DbUser"
    } else {
        return "-E"  # Windows Authentication
    }
}

# Backup database
function Invoke-Backup {
    Write-Header "גיבוי בסיס נתונים"
    
    # Create backup directory
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $BackupDir "kkl_forest_$timestamp.bak"
    
    Write-Host "Creating backup: $backupFile"
    
    $auth = Get-SqlCmdAuth
    $query = "BACKUP DATABASE [$DbName] TO DISK = '$backupFile'"
    
    $result = & sqlcmd -S $DbServer $auth -Q $query 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Message "Backup failed!"
        Write-Host $result
        exit 1
    }
    
    Write-Success "Backup created: $backupFile"
    return $backupFile
}

# Data quality check
function Invoke-DataQualityCheck {
    Write-Header "בדיקת איכות נתונים"
    
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = Join-Path $BackupDir "data_quality_check_$timestamp.txt"
    
    $scriptFile = Join-Path $MigrationsDir "01_data_quality_check.sql"
    
    if (-not (Test-Path $scriptFile)) {
        Write-Error-Message "Script not found: $scriptFile"
        exit 1
    }
    
    Write-Host "Running data quality check..."
    Write-Host "Output: $outputFile"
    
    $auth = Get-SqlCmdAuth
    $result = & sqlcmd -S $DbServer -d $DbName $auth -i $scriptFile -o $outputFile 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Message "Data quality check failed!"
        Write-Host $result
        exit 1
    }
    
    Write-Success "Data quality check completed!"
    Write-Warning-Message "Please review: $outputFile"
    
    # Show critical issues
    Write-Host ""
    Write-Host "Critical issues found:"
    $criticalIssues = Select-String -Path $outputFile -Pattern "\*\*\*"
    if ($criticalIssues) {
        $criticalIssues | ForEach-Object { Write-Host $_.Line -ForegroundColor Yellow }
    } else {
        Write-Host "None" -ForegroundColor Green
    }
    
    return $outputFile
}

# Permissions migration
function Invoke-PermissionsMigration {
    Write-Header "מיגרציית הרשאות"
    
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = Join-Path $BackupDir "permissions_migration_$timestamp.txt"
    
    $scriptFile = Join-Path $MigrationsDir "02_permissions_migration.sql"
    
    if (-not (Test-Path $scriptFile)) {
        Write-Error-Message "Script not found: $scriptFile"
        exit 1
    }
    
    Write-Host "Running permissions migration..."
    Write-Host "Output: $outputFile"
    
    $auth = Get-SqlCmdAuth
    $result = & sqlcmd -S $DbServer -d $DbName $auth -i $scriptFile -o $outputFile 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Message "Permissions migration failed!"
        Write-Warning-Message "Check output: $outputFile"
        Write-Host $result
        exit 1
    }
    
    Write-Success "Permissions migration completed!"
    
    # Show migration log
    Write-Host ""
    Write-Host "Migration log:"
    $logQuery = "SELECT TOP 10 * FROM migration_log ORDER BY id DESC"
    & sqlcmd -S $DbServer -d $DbName $auth -Q $logQuery
    
    return $outputFile
}

# Suppliers migration
function Invoke-SuppliersMigration {
    Write-Header "מיגרציית ספקים"
    
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = Join-Path $BackupDir "suppliers_migration_$timestamp.txt"
    
    $scriptFile = Join-Path $MigrationsDir "03_supplier_migration.sql"
    
    if (-not (Test-Path $scriptFile)) {
        Write-Error-Message "Script not found: $scriptFile"
        exit 1
    }
    
    Write-Host "Running suppliers migration..."
    Write-Host "Output: $outputFile"
    
    $auth = Get-SqlCmdAuth
    $result = & sqlcmd -S $DbServer -d $DbName $auth -i $scriptFile -o $outputFile 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Message "Suppliers migration failed!"
        Write-Warning-Message "Check output: $outputFile"
        Write-Host $result
        exit 1
    }
    
    Write-Success "Suppliers migration completed!"
    
    return $outputFile
}

# Update Python code
function Invoke-PythonUpdate {
    Write-Header "עדכון קוד Python"
    
    $scriptFile = Join-Path $MigrationsDir "04_update_python_code.py"
    
    if (-not (Test-Path $scriptFile)) {
        Write-Error-Message "Script not found: $scriptFile"
        exit 1
    }
    
    Write-Host "Running Python code update script..."
    
    Push-Location app_backend
    
    try {
        python database\migrations\04_update_python_code.py
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Message "Python code update failed!"
            Pop-Location
            exit 1
        }
        
        Write-Success "Python code update completed!"
        Write-Warning-Message "Please review and update routers manually!"
    }
    finally {
        Pop-Location
    }
}

# Main
function Main {
    Test-SqlCmd
    
    switch ($Step) {
        "Backup" {
            Invoke-Backup
        }
        "Check" {
            Invoke-DataQualityCheck
        }
        "Perms" {
            Invoke-PermissionsMigration
        }
        "Suppliers" {
            Invoke-SuppliersMigration
        }
        "Python" {
            Invoke-PythonUpdate
        }
        "All" {
            Write-Warning-Message "Running ALL steps - are you sure? (Press Ctrl+C to cancel)"
            Start-Sleep -Seconds 5
            
            # Backup
            $backupFile = Invoke-Backup
            
            # Check
            $checkFile = Invoke-DataQualityCheck
            
            # Confirm
            Write-Warning-Message "Review data quality check results before continuing!"
            $confirm = Read-Host "Continue with migration? (yes/no)"
            if ($confirm -ne "yes") {
                Write-Host "Migration cancelled."
                exit 0
            }
            
            # Migrations
            $permsFile = Invoke-PermissionsMigration
            $suppliersFile = Invoke-SuppliersMigration
            Invoke-PythonUpdate
            
            Write-Success "All steps completed!"
            
            # Summary
            Write-Host ""
            Write-Header "Summary"
            Write-Host "Backup: $backupFile"
            Write-Host "Data Quality Check: $checkFile"
            Write-Host "Permissions Migration: $permsFile"
            Write-Host "Suppliers Migration: $suppliersFile"
        }
        "Help" {
            Write-Host ""
            Write-Host "Usage: .\run_migration.ps1 -Step <step> [-DbServer <server>] [-DbName <name>] [-DbUser <user>]"
            Write-Host ""
            Write-Host "Steps:"
            Write-Host "  Backup    - גיבוי הבסיס"
            Write-Host "  Check     - בדיקת איכות נתונים"
            Write-Host "  Perms     - מיגרציית הרשאות"
            Write-Host "  Suppliers - מיגרציית ספקים"
            Write-Host "  Python    - עדכון קוד Python"
            Write-Host "  All       - הכל ברצף (זהירות!)"
            Write-Host ""
            Write-Host "Examples:"
            Write-Host "  .\run_migration.ps1 -Step Backup"
            Write-Host "  .\run_migration.ps1 -Step Check"
            Write-Host "  .\run_migration.ps1 -Step All -DbServer localhost -DbName kkl_forest"
            Write-Host ""
            Write-Host "Options:"
            Write-Host "  -DbServer   Database server (default: localhost)"
            Write-Host "  -DbName     Database name (default: kkl_forest)"
            Write-Host "  -DbUser     Database user (default: Windows Authentication)"
            Write-Host "  -BackupDir  Backup directory (default: .\backups)"
            Write-Host ""
        }
    }
}

# Run
Main


