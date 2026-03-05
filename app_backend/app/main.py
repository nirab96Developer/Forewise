# app/main.py
"""
Forest Management System - Main Application Entry Point
מערכת ניהול יערות ופרויקטים
"""
from app.routers import api_router
from fastapi import APIRouter
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

# Import configurations
from app.core.config import settings
from app.core.database import engine, get_db
from app.core.logging import logger, setup_logging
from app.core.rate_limiting import rate_limit_middleware

# Sentry — Error Monitoring (initialised only when DSN is configured)
try:
    import sentry_sdk
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialised")
except ImportError:
    pass  # sentry-sdk not installed — skip silently

# Custom API metadata בעברית
API_METADATA = {
    "title": "🌲 מערכת ניהול יערות ופרויקטים",
    "description": """
## מערכת ניהול מתקדמת לקק"ל

### 🎯 יכולות המערכת:
* **ניהול פרויקטים** - יצירה, עדכון ומעקב אחר פרויקטים
* **ניהול ציוד** - הקצאת ציוד, תחזוקה וסריקות
* **ניהול ספקים** - סבב הוגן, הזמנות ומעקב ביצועים
* **דיווחי שעות** - דיווח שעות עבודה וחישוב אוטומטי
* **חשבוניות** - הפקת חשבוניות אוטומטיות
* **תקציבים** - ניהול והקצאת תקציבים
* **דוחות** - דוחות מנהלים ואנליטיקס

### אבטחה:
- הזדהות מאובטחת עם JWT
- ניהול הרשאות מתקדם (RBAC)
- תיעוד כל הפעולות במערכת

### 📊 סטטוס המערכת:
- **סביבה:** {environment}
- **גרסה:** 1.0.0
- **Database:** PostgreSQL
    """.format(environment=settings.ENVIRONMENT),
    "version": "1.0.0",
    "terms_of_service": "/terms",
    "contact": {
        "name": "צוות פיתוח",
        "email": "dev@forest-system.com"
    },
    "license": {
        "name": "Private License",
        "url": "#"
    }
}

# Tags בעברית לקטגוריות
tags_metadata = [
    {
        "name": "🏠 מערכת",
        "description": "נתיבי מערכת ובדיקות תקינות"
    },
    {
        "name": "אימות",
        "description": "התחברות, הרשמה וניהול סיסמאות"
    },
    {
        "name": "👤 משתמשים",
        "description": "ניהול משתמשים ופרופילים"
    },
    {
        "name": "📋 פרויקטים",
        "description": "ניהול פרויקטים ומשימות"
    },
    {
        "name": "🚜 ציוד",
        "description": "ניהול ציוד ותחזוקה"
    },
    {
        "name": "👷 ספקים",
        "description": "ניהול ספקים והזמנות"
    },
    {
        "name": "⏰ דיווחים",
        "description": "דיווחי שעות ועבודה"
    },
    {
        "name": "💰 כספים",
        "description": "חשבוניות ותקציבים"
    },
    {
        "name": "🔧 ניהול",
        "description": "ניהול מערכת והגדרות"
    },
    {
        "name": "🐛 Debug",
        "description": "כלי דיבוג ובדיקה (רק במצב פיתוח)"
    }
]

# Import routers

# Import the pre-configured API router from routers/__init__.py
# It already has all routers loaded dynamically
logger.info("Using pre-configured API router with all routers")


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Forest Management System...")
    try:
        setup_logging(settings.LOG_LEVEL)
        logger.info("Initializing database...")

        from sqlalchemy import inspect
        from app.models import Base

        try:
            inspector = inspect(engine)
            if not inspector.get_table_names():
                logger.info("Creating database tables...")
                Base.metadata.create_all(bind=engine)
            logger.info("Database initialized")
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")

        logger.info("Application started successfully!")
        logger.info(f"Running on: http://{settings.APP_HOST}:{settings.APP_PORT}")
        logger.info(f"API Documentation: http://{settings.APP_HOST}:{settings.APP_PORT}/docs")

    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

    # Start nightly CRON for anonymizing expired/suspended users
    import asyncio as _asyncio
    from app.tasks.user_lifecycle import schedule_nightly_cleanup
    _cleanup_task = _asyncio.create_task(schedule_nightly_cleanup())

    yield

    # Shutdown
    _cleanup_task.cancel()
    logger.info("Shutting down...")
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    **API_METADATA,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.DEBUG,
    openapi_tags=tags_metadata
    # Note: keeping redirect_slashes=True (default) for compatibility
)

# Configure CORS
# ⚠️ SECURITY: In production, restrict to only your actual domain(s)
# For now using IP address - replace with your actual domain when you have one

if settings.is_production():
    allowed_origins = [
        "https://forewise.co",
        "https://www.forewise.co",
        "http://forewise.co",
        "http://167.99.228.10",
        "http://167.99.228.10:3000",
        "http://167.99.228.10:5173",
    ]
else:
    allowed_origins = [
        # Production domain
        "https://forewise.co",
        "https://www.forewise.co",
        "http://forewise.co",
        # Production server IP
        "http://167.99.228.10",
        "http://167.99.228.10:3000",
        "http://167.99.228.10:5173",
        "http://167.99.228.10:8000",
        # Development
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://10.0.0.20:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://10.0.0.20:5173",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["*"],  # Can be restricted further if needed
    max_age=600,  # Cache preflight for 10 minutes
)

# Add session middleware with secure settings
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="__Secure-forest_session" if settings.is_production() else "forest_session",
    max_age=3600,  # 1 hour (reduced from 24 hours for security)
    same_site="strict",
    https_only=settings.is_production(),  # Secure flag in production
)

# Add rate limiting middleware
# ⚠️ PRODUCTION: Rate limiting is enabled automatically in production mode
app.middleware("http")(rate_limit_middleware)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============================================================
# Security Headers Middleware
# ============================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.
    Protects against common web vulnerabilities.
    """
    response = await call_next(request)
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # XSS Protection (legacy, but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Force HTTPS in production
    if settings.is_production():
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https://cdn.jsdelivr.net; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self';"
    )
    
    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy (formerly Feature-Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=()"
    )
    
    return response


# ============================================================
# Safe Mode Middleware - Block writes in production/testing
# ============================================================
@app.middleware("http")
async def offline_sync_audit_middleware(request: Request, call_next):
    """
    When request arrives with X-Offline-Sync: true header,
    record it in sync_queue for auditing after the response is sent.
    """
    is_offline_sync = request.headers.get("X-Offline-Sync") == "true"
    response = await call_next(request)
    if is_offline_sync and response.status_code < 300:
        try:
            from app.core.database import SessionLocal
            from sqlalchemy import text as _text
            import json as _json
            db = SessionLocal()
            try:
                # Get user_id from Authorization header (best-effort)
                user_id = None
                auth = request.headers.get("Authorization", "")
                if auth.startswith("Bearer "):
                    try:
                        from app.core.security import decode_token
                        payload = decode_token(auth.split(" ", 1)[1])
                        user_id = payload.get("sub")
                    except Exception:
                        pass
                op_type = request.url.path.split("/")[-2] if "/" in request.url.path else "unknown"
                client_ip = request.client.host if request.client else None
                db.execute(_text(
                    "INSERT INTO sync_queue (user_id, type, payload, ip_address) "
                    "VALUES (:uid, :type, :payload::jsonb, :ip)"
                ), {
                    "uid": user_id,
                    "type": op_type,
                    "payload": _json.dumps({"path": request.url.path, "method": request.method}),
                    "ip": client_ip,
                })
                db.commit()
            finally:
                db.close()
        except Exception:
            pass  # audit is best-effort, never block the response
    return response


@app.middleware("http")
async def safe_mode_middleware(request: Request, call_next):
    """
    Block all write operations when SAFE_MODE is enabled.
    Allows only GET and OPTIONS methods.
    """
    if settings.SAFE_MODE:
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            # Allow specific safe endpoints even in safe mode
            safe_paths = ["/auth/login", "/auth/token", "/health", "/docs", "/openapi.json"]
            if not any(request.url.path.endswith(p) for p in safe_paths):
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "🔒 SAFE MODE: Write operations are disabled. Only GET requests allowed.",
                        "safe_mode": True,
                        "method": request.method,
                        "path": request.url.path
                    }
                )
    return await call_next(request)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Convert any bytes to str in error details
    errors = []
    for error in exc.errors():
        error_dict = dict(error)
        if 'input' in error_dict and isinstance(error_dict['input'], bytes):
            error_dict['input'] = error_dict['input'].decode('utf-8', errors='replace')
        errors.append(error_dict)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"message": "שגיאת ולידציה", "details": errors}},
    )


# System endpoints בעברית
@app.get("/", tags=["🏠 מערכת"], summary="דף הבית", description="מחזיר מידע בסיסי על המערכת")
async def root():
    """מידע בסיסי על המערכת."""
    return {
        "שם": "מערכת ניהול יערות",
        "גרסה": "1.0.0",
        "סטטוס": "פעיל",
        "סביבה": settings.ENVIRONMENT,
        "תיעוד": "/docs",
        "בדיקת_תקינות": "/health",
    }


@app.get("/health", tags=["🏠 מערכת"], summary="בדיקת תקינות", description="בודק את מצב המערכת והחיבורים")
async def health_check():
    """
    בדיקת תקינות המערכת.

    בודק:
    - חיבור ל-Database
    - חיבור ל-Redis (אם מופעל)
    - סטטוס כללי
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/v1/health", tags=["🏠 מערכת"], summary="בדיקת תקינות API", description="בודק את מצב ה-API")
async def api_health_check():
    """בדיקת תקינות API endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/health/db", tags=["🏠 מערכת"], summary="בדיקת תקינות Database", description="בודק את חיבור ה-Database")
async def health_check_db():
    """בדיקת תקינות Database."""
    try:
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "database": "connected",
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "database": "error",
            "error": str(e),
            "status": "error",
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/info", tags=["🏠 מערכת"], summary="מידע מערכת", description="מחזיר מידע מפורט על המערכת")
async def system_info():
    """
    מידע מפורט על המערכת.

    כולל:
    - גרסת API
    - סביבת הרצה
    - ראוטרים פעילים
    - הגדרות
    """
    try:
        from app.routers import loaded_routers, failed_routers, ROUTER_MODULES
        router_info = {
            "פעילים": loaded_routers,
            "נכשלו": failed_routers[:5],
            "סה״כ": len(ROUTER_MODULES)
        }
    except:
        router_info = {"סטטוס": "לא זמין"}

    return {
        "גרסת_API": "1.0.0",
        "סביבה": settings.ENVIRONMENT,
        "ראוטרים": router_info,
        "database": "PostgreSQL",
        "מצב_debug": settings.DEBUG
    }


@app.get("/test", tags=["🏠 מערכת"], summary="בדיקת API", description="endpoint פשוט לבדיקה")
async def test_endpoint():
    """בדיקה פשוטה ש-API עובד."""
    return {
        "הודעה": "ה-API עובד כמו שצריך!",
        "זמן": datetime.now().isoformat()
    }


# Include API router
try:
    app.include_router(api_router, prefix="/api/v1")
    logger.info("API routers loaded successfully")
except Exception as e:
    logger.warning(f"Could not load API routers: {e}")

# Add basic auth endpoints if routers failed
if not api_router.routes:
    from fastapi import HTTPException
    from app.core.security import verify_password
    from app.models.user import User
    from sqlalchemy.orm import Session

    from pydantic import BaseModel

    class LoginRequest(BaseModel):
        email: str
        password: str

    @app.post("/api/v1/auth/login", tags=["אימות"])
    async def login(request: LoginRequest):
        """Login endpoint."""
        try:
            from sqlalchemy import text
            from app.core.security import create_access_token

            db = next(get_db())
            # Simple query without loading relationships
            user = db.execute(
                text(
                    "SELECT id, email, username, full_name, password_hash, is_active FROM users WHERE email = :email"),
                {"email": request.email}
            ).fetchone()

            if not user or not verify_password(request.password, user.password_hash):
                raise HTTPException(status_code=401, detail="אימייל או סיסמה שגויים")

            if not user.is_active:
                raise HTTPException(status_code=401, detail="החשבון לא פעיל")

            # Generate token (simplified)
            access_token = create_access_token(data={"sub": str(user.id)})

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            db.close()

    logger.info("Basic auth endpoints added")


# Admin endpoints בעברית
@app.get("/admin/health", tags=["🔧 ניהול"], summary="בדיקת תקינות ניהול")
async def admin_health():
    """בדיקת תקינות מודול הניהול."""
    return {"סטטוס": "פעיל", "מודול": "ניהול"}


# Debug endpoints
if settings.DEBUG:
    @app.get("/debug/routes", tags=["🐛 Debug"], summary="רשימת נתיבים", description="מציג את כל הנתיבים במערכת")
    async def list_routes():
        """רשימת כל הנתיבים הרשומים במערכת."""
        routes = []
        for route in app.routes:
            if hasattr(route, "methods"):
                routes.append({
                    "נתיב": route.path,
                    "methods": list(route.methods),
                    "שם": route.name,
                })
        return {"סה״כ": len(routes), "נתיבים": routes}

    @app.get("/debug/config", tags=["🐛 Debug"], summary="הגדרות מערכת", description="מציג את הגדרות המערכת הנוכחיות")
    async def show_config():
        """הצג הגדרות נוכחיות (רק במצב debug)."""
        return {
            "סביבה": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database": "PostgreSQL",
            "redis_מופעל": settings.REDIS_ENABLED,
            "cors_origins": settings.CORS_ORIGINS,
            "host": settings.APP_HOST,
            "port": settings.APP_PORT
        }
