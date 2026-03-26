#!/bin/bash
# =========================================================================
# סקריפט אוטומציה למיגרציה - קק"ל
# =========================================================================
# שימוש: ./run_migration.sh [step]
#
# Steps:
#   backup    - גיבוי הבסיס
#   check     - בדיקת איכות נתונים
#   perms     - מיגרציית הרשאות
#   suppliers - מיגרציית ספקים
#   python    - עדכון קוד Python
#   all       - הכל ברצף (זהירות!)
# =========================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (עדכן לפי הסביבה שלך!)
DB_SERVER="${DB_SERVER:-localhost}"
DB_NAME="${DB_NAME:-forewise_prod}"
DB_USER="${DB_USER:-sa}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
MIGRATIONS_DIR="./app_backend/database/migrations"

# Functions
print_header() {
    echo ""
    echo "================================================================="
    echo -e "${GREEN}$1${NC}"
    echo "================================================================="
    echo ""
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check if sqlcmd is available
check_sqlcmd() {
    if ! command -v sqlcmd &> /dev/null; then
        print_error "sqlcmd not found! Please install SQL Server command-line tools."
        exit 1
    fi
}

# Backup database
backup_db() {
    print_header "גיבוי בסיס נתונים"
    
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/forewise_prod_$(date +%Y%m%d_%H%M%S).bak"
    
    echo "Creating backup: $BACKUP_FILE"
    
    sqlcmd -S "$DB_SERVER" -d "$DB_NAME" -U "$DB_USER" -Q \
        "BACKUP DATABASE [$DB_NAME] TO DISK = '$BACKUP_FILE'" \
        || {
            print_error "Backup failed!"
            exit 1
        }
    
    print_success "Backup created: $BACKUP_FILE"
}

# Data quality check
check_data_quality() {
    print_header "בדיקת איכות נתונים"
    
    OUTPUT_FILE="$BACKUP_DIR/data_quality_check_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "Running data quality check..."
    echo "Output: $OUTPUT_FILE"
    
    sqlcmd -S "$DB_SERVER" -d "$DB_NAME" -U "$DB_USER" \
        -i "$MIGRATIONS_DIR/01_data_quality_check.sql" \
        -o "$OUTPUT_FILE" \
        || {
            print_error "Data quality check failed!"
            exit 1
        }
    
    print_success "Data quality check completed!"
    print_warning "Please review: $OUTPUT_FILE"
    
    # Show critical issues
    echo ""
    echo "Critical issues found:"
    grep -i "***" "$OUTPUT_FILE" || echo "None"
}

# Permissions migration
migrate_permissions() {
    print_header "מיגרציית הרשאות"
    
    OUTPUT_FILE="$BACKUP_DIR/permissions_migration_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "Running permissions migration..."
    echo "Output: $OUTPUT_FILE"
    
    sqlcmd -S "$DB_SERVER" -d "$DB_NAME" -U "$DB_USER" \
        -i "$MIGRATIONS_DIR/02_permissions_migration.sql" \
        -o "$OUTPUT_FILE" \
        || {
            print_error "Permissions migration failed!"
            print_warning "Check output: $OUTPUT_FILE"
            exit 1
        }
    
    print_success "Permissions migration completed!"
    
    # Show summary
    echo ""
    echo "Migration log:"
    sqlcmd -S "$DB_SERVER" -d "$DB_NAME" -U "$DB_USER" \
        -Q "SELECT TOP 10 * FROM migration_log ORDER BY id DESC"
}

# Suppliers migration
migrate_suppliers() {
    print_header "מיגרציית ספקים"
    
    OUTPUT_FILE="$BACKUP_DIR/suppliers_migration_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "Running suppliers migration..."
    echo "Output: $OUTPUT_FILE"
    
    sqlcmd -S "$DB_SERVER" -d "$DB_NAME" -U "$DB_USER" \
        -i "$MIGRATIONS_DIR/03_supplier_migration.sql" \
        -o "$OUTPUT_FILE" \
        || {
            print_error "Suppliers migration failed!"
            print_warning "Check output: $OUTPUT_FILE"
            exit 1
        }
    
    print_success "Suppliers migration completed!"
}

# Update Python code
update_python() {
    print_header "עדכון קוד Python"
    
    cd app_backend
    
    echo "Running Python code update script..."
    
    python database/migrations/04_update_python_code.py \
        || {
            print_error "Python code update failed!"
            exit 1
        }
    
    cd ..
    
    print_success "Python code update completed!"
    print_warning "Please review and update routers manually!"
}

# Main
main() {
    check_sqlcmd
    
    STEP="${1:-help}"
    
    case "$STEP" in
        backup)
            backup_db
            ;;
        check)
            check_data_quality
            ;;
        perms)
            migrate_permissions
            ;;
        suppliers)
            migrate_suppliers
            ;;
        python)
            update_python
            ;;
        all)
            print_warning "Running ALL steps - are you sure? (Ctrl+C to cancel)"
            sleep 5
            
            backup_db
            check_data_quality
            
            print_warning "Review data quality check results before continuing!"
            read -p "Continue with migration? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                echo "Migration cancelled."
                exit 0
            fi
            
            migrate_permissions
            migrate_suppliers
            update_python
            
            print_success "All steps completed!"
            ;;
        help|*)
            echo "Usage: $0 [step]"
            echo ""
            echo "Steps:"
            echo "  backup    - גיבוי הבסיס"
            echo "  check     - בדיקת איכות נתונים"
            echo "  perms     - מיגרציית הרשאות"
            echo "  suppliers - מיגרציית ספקים"
            echo "  python    - עדכון קוד Python"
            echo "  all       - הכל ברצף (זהירות!)"
            echo ""
            echo "Examples:"
            echo "  $0 backup      # Create backup only"
            echo "  $0 check       # Run data quality check"
            echo "  $0 all         # Run everything"
            exit 1
            ;;
    esac
}

main "$@"


