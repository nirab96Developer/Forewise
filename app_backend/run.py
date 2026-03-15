# run.py
"""
Runner script for Forest Management System
מערכת ניהול יערות - סקריפט הרצה
"""
import os
import sys
import io
import uvicorn
from pathlib import Path

# Fix encoding issues on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import logger


def kill_existing_port(port: int):
    """Kill any process using the given port to prevent Errno 98."""
    import subprocess
    try:
        result = subprocess.run(
            ["fuser", "-k", f"{port}/tcp"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            import time
            time.sleep(1)
            print(f"Killed existing process on port {port}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def main():
    """Run the application."""
    kill_existing_port(settings.APP_PORT)

    print("Forest Management System")
    print("=" * 50)
    
    # Environment info
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Host: {settings.APP_HOST}")
    print(f"Port: {settings.APP_PORT}")
    print(f"API Docs: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    print("=" * 50)
    
    logger.info(f"Starting server on http://{settings.APP_HOST}:{settings.APP_PORT}")
    logger.info(f"API Documentation: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Configure uvicorn based on environment
    if settings.ENVIRONMENT == "development":
        # Development settings
        uvicorn.run(
            "app.main:app",
            host=settings.APP_HOST,
            port=settings.APP_PORT,
            reload=settings.RELOAD,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
            reload_dirs=["app"],
        )
    else:
        # Production settings
        uvicorn.run(
            "app.main:app",
            host=settings.APP_HOST,
            port=settings.APP_PORT,
            reload=False,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=True,
            workers=settings.WORKERS,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        logger.info("Server stopped by user")
    except Exception as e:
        print(f"Server failed to start: {e}")
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)
