#!/bin/bash
# start_production.sh
# Forewise - Production Startup Script
# מערכת ניהול יערות - סקריפט הפעלה לפרודקשן

set -e

echo "🌲 Forewise - Production Startup"
echo "================================================"

# Detect virtual environment (venv or .venv)
if [ -d "venv/bin" ]; then
    VENV_DIR="venv"
elif [ -d ".venv/bin" ]; then
    VENV_DIR=".venv"
else
    echo "❌ Virtual environment not found (checked venv/ and .venv/)"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment ($VENV_DIR)..."
source "$VENV_DIR/bin/activate" || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

# Set production environment variables
export ENVIRONMENT=production
export DEBUG=False
export LOG_LEVEL=INFO
export WORKERS=4

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Using default settings."
fi

# Check database connection
echo "🔍 Checking database connection..."
python -c "
from app.core.database import check_connection
if check_connection():
    print('✅ Database connection successful')
else:
    print('❌ Database connection failed')
    exit(1)
" || exit 1

# Run database migrations (if needed)
echo "📊 Running database migrations..."
alembic upgrade head || echo "⚠️  Migration warning (continuing...)"

# Start the server
echo "🚀 Starting production server..."
echo "📊 Environment: $ENVIRONMENT"
echo "🔧 Debug: $DEBUG"
echo "👥 Workers: $WORKERS"
echo "📚 API Docs: http://0.0.0.0:8000/docs"
echo "================================================"

# Use Gunicorn for production — nohup background so it survives SSH disconnects
LOG_FILE="$(pwd)/logs/gunicorn.log"
mkdir -p "$(pwd)/logs"

nohup "$VENV_DIR/bin/gunicorn" -c gunicorn.conf.py wsgi:application \
  >> "$LOG_FILE" 2>&1 &

GPID=$!
echo "🌲 Gunicorn started — PID: $GPID"
echo "📄 Log: $LOG_FILE"

# Wait and verify
sleep 5
if kill -0 "$GPID" 2>/dev/null; then
    echo "✅ Gunicorn is running (PID $GPID)"
    curl -s --max-time 5 http://localhost:8000/api/v1/health && echo ""
else
    echo "❌ Gunicorn failed to start — check $LOG_FILE"
    tail -20 "$LOG_FILE"
    exit 1
fi

