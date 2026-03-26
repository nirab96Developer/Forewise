# wsgi.py
"""
WSGI entry point for production deployment
מערכת ניהול יערות - נקודת כניסה לפרודקשן
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for production
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DEBUG", "False")

try:
    from app.main import app
    from app.core.config import settings
    
    # WSGI application for Gunicorn/uWSGI
    application = app
    
    # Log startup info
    print("Forewise WSGI loaded")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Host: {settings.APP_HOST}:{settings.APP_PORT}")
    
except Exception as e:
    print(f"Failed to load WSGI application: {e}")
    raise


if __name__ == "__main__":
    # For development/testing
    import uvicorn
    
    print("Starting development server...")
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
