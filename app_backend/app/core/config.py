# app/core/config.py
"""
Application configuration
"""
import json
import logging
import logging.config
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, field_validator, Field


class Settings(BaseSettings):
    """
    הגדרות המערכת המרכזיות.

    קורא הגדרות מקובץ .env וממשתני סביבה, עם תמיכה בהמרות סוגי נתונים
    והתמודדות עם פורמטים שונים.
    """

    # ==========================================
    # הגדרות כלליות
    # ==========================================
    APP_NAME: str = "Reports Management System"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Project and Equipment Reports Management System"
    PROJECT_NAME: str = ""
    ENVIRONMENT: str = "development"

    # ==========================================
    # Sentry — Error Monitoring
    # ==========================================
    SENTRY_DSN: Optional[str] = None  # מלא אחרי יצירת חשבון Sentry
    DEBUG: bool = False
    
    # ==========================================
    # Safe Mode - חסימת כתיבות בפרודקשן
    # ==========================================
    SAFE_MODE: bool = Field(
        default=False, 
        alias="APP_SAFE_MODE",
        description="When True, blocks all write operations (POST/PUT/PATCH/DELETE)"
    )

    # ==========================================
    # הגדרות API
    # ==========================================
    API_V1_STR: str = "/api/v1"
    ROOT_PATH: str = ""

    # ==========================================
    # הגדרות מסד נתונים
    # ==========================================
    # ⚠️ CRITICAL SECURITY: Never hardcode database credentials!
    # Use environment variables or Azure Key Vault
    DATABASE_URL: str  # No default - MUST be provided via environment
    TEST_DATABASE_URL: str = "postgresql://test_user:test_pass@localhost:5432/test_db"
    TESTING: bool = False

    # הגדרות חיבור
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # הגדרות בדיקות
    TEST_DB_POOL_SIZE: int = 2
    TEST_DB_MAX_OVERFLOW: int = 5

    # ==========================================
    # הגדרות אבטחה
    # ==========================================
    # ⚠️ CRITICAL SECURITY: SECRET_KEY must be set via environment variable!
    # Generate strong key: python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str  # No default - MUST be provided
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 60 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    MIN_PASSWORD_LENGTH: int = 8

    # ==========================================
    # הגדרות שרת
    # ==========================================
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    FRONTEND_URL: str = "http://167.99.228.10"  # כתובת הפרונטאנד בפרודקשן
    WORKERS: int = 4
    RELOAD: bool = False  # Disabled to prevent infinite reload loop
    LOG_LEVEL: str = "INFO"

    # ==========================================
    # הגדרות CORS
    # ==========================================
    BACKEND_CORS_ORIGINS: List[str] = [
        # Production
        "https://forewise.co",
        "https://www.forewise.co",
        # Local development
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://10.0.0.20:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://10.0.0.20:5174",
    ]
    # Alias for backward compatibility
    CORS_ORIGINS: List[str] = BACKEND_CORS_ORIGINS
    CORS_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_HEADERS: List[str] = ["*"]
    CORS_MAX_AGE: int = 600
    ALLOWED_HOSTS: List[str] = ["*"]

    # ==========================================
    # הגדרות תיעוד API
    # ==========================================
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    SWAGGER_UI_ENABLED: bool = True

    # ==========================================
    # הגדרות אימייל
    # ==========================================
    # ⚠️ SECURITY: Never hardcode credentials!
    # Use environment variables or Azure Key Vault
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Must be set via environment variable
    SMTP_PASSWORD: str = ""  # Must be set via environment variable
    SMTP_USE_TLS: bool = True
    SMTP_TIMEOUT: int = 30
    EMAIL_FROM: str = ""  # Must be set via environment variable
    EMAIL_FROM_NAME: str = "Forest Management System"
    # ==========================================
    # הגדרות SMS
    # ==========================================
    SMS_API_KEY: Optional[str] = None
    SMS_API_URL: str = "https://api.sms4free.co.il/api/send"
    SMS_SENDER_NAME: str = "ForestSys"

    # ==========================================
    # הגדרות העלאת קבצים
    # ==========================================
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB ברירת מחדל
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "jpg",
        "jpeg",
        "png",
    ]

    # ==========================================
    # הגדרות ביצועים
    # ==========================================
    SLOW_QUERY_THRESHOLD: float = 1.0
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # ==========================================
    # הגדרות פיתוח וניטור
    # ==========================================
    ENABLE_PROFILING: bool = False
    ENABLE_ERROR_TRACKING: bool = True
    ERROR_TRACKING_LEVEL: str = "WARNING"

    # ==========================================
    # הגדרות Redis
    # ==========================================
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False

    # ==========================================
    # הגדרות מנהל
    # ==========================================
    DEFAULT_ADMIN_EMAIL: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""
    FIRST_SUPERUSER_EMAIL: str = ""
    FIRST_SUPERUSER_PASSWORD: str = ""

    # ==========================================
    # הגדרות תחום עסקי
    # ==========================================
    EQUIPMENT_STATUS: List[str] = ["available", "in_use", "maintenance", "retired"]
    EQUIPMENT_TYPES: List[str] = ["vehicle", "tool", "machinery", "office", "safety"]
    PROJECT_STATUS: List[str] = [
        "planned",
        "active",
        "on_hold",
        "completed",
        "cancelled",
    ]
    PROJECT_PRIORITIES: List[str] = ["low", "medium", "high", "urgent"]

    # ==========================================
    # הגדרות דיווחים
    # ==========================================
    REPORT_TYPES: List[str] = [
        "daily",
        "weekly",
        "monthly",
        "quarterly",
        "annual",
        "custom",
    ]
    REPORT_FORMATS: List[str] = ["pdf", "excel", "csv", "json", "html"]
    REPORT_STORAGE_DAYS: int = 90
    AUTO_REPORT_GENERATION: bool = True
    REPORT_TEMPLATE_PATH: str = "/app/templates/reports"

    # ==========================================
    # הגדרות API חיצוניים
    # ==========================================
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    # ==========================================
    # הגדרות לוקליזציה
    # ==========================================
    DEFAULT_LANGUAGE: str = "he"
    DEFAULT_REGION: str = "IL"

    # ==========================================
    # הגדרות Logging נוספות
    # ==========================================
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_FILE_MAX_BYTES: int = 10485760  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5

    # ==========================================
    # הגדרות Cache
    # ==========================================
    CACHE_TTL_SECONDS: int = 300  # 5 minutes
    CACHE_KEY_PREFIX: str = "rms:"  # Reports Management System

    # ==========================================
    # הגדרות תזמון משימות
    # ==========================================
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "Asia/Jerusalem"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True, 
        extra="ignore",
        # Prevent automatic JSON parsing for List fields
        env_parse_none_str="None"
    )
    
    @model_validator(mode='before')
    @classmethod
    def parse_cors_origins_before(cls, data: Any) -> Any:
        """Parse CORS_ORIGINS from .env before Pydantic tries to parse it as JSON."""
        if not isinstance(data, dict):
            return data
        
        # Get CORS_ORIGINS value from the data dict
        if "CORS_ORIGINS" in data:
            value = data["CORS_ORIGINS"]
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    data["CORS_ORIGINS"] = []
                elif not (value.startswith("[") and value.endswith("]")):
                    # זה לא JSON, המר לרשימה מופרדת בפסיקים
                    if "," in value:
                        items = [item.strip() for item in value.split(",") if item.strip()]
                        data["CORS_ORIGINS"] = items if items else []
                    else:
                        data["CORS_ORIGINS"] = [value]
                # אם זה JSON, תן ל-Pydantic לטפל בזה
        
        return data

    def __init__(self, **data):
        # טיפול במיוחד בשדה MAX_FILE_SIZE - ניקוי הערות בקובץ .env
        if "MAX_FILE_SIZE" in data and isinstance(data["MAX_FILE_SIZE"], str):
            try:
                # ניסיון לתקן את הערך עם הערה
                if "#" in data["MAX_FILE_SIZE"]:
                    data["MAX_FILE_SIZE"] = data["MAX_FILE_SIZE"].split("#")[0].strip()
            except ValueError:
                # אם נכשל, השתמש בערך ברירת מחדל
                data["MAX_FILE_SIZE"] = 10485760

        # טיפול בקישור מסד נתונים שעשוי להכיל הערות
        if "DATABASE_URL" in data and isinstance(data["DATABASE_URL"], str):
            if "#" in data["DATABASE_URL"]:
                data["DATABASE_URL"] = data["DATABASE_URL"].split("#")[0].strip()

        # טיפול ב-CORS_ORIGINS לפני ש-Pydantic מנסה לפרסר כ-JSON
        if "CORS_ORIGINS" in data:
            value = data["CORS_ORIGINS"]
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    data["CORS_ORIGINS"] = []
                elif not (value.startswith("[") and value.endswith("]")):
                    # זה לא JSON, המר לרשימה מופרדת בפסיקים
                    if "," in value:
                        data["CORS_ORIGINS"] = [item.strip() for item in value.split(",") if item.strip()]
                    else:
                        data["CORS_ORIGINS"] = [value]
                # אם זה JSON, תן ל-Pydantic לטפל בזה

        super().__init__(**data)

        # הוסף PROJECT_NAME אם הוא ריק
        if not self.PROJECT_NAME:
            self.PROJECT_NAME = self.APP_NAME

        # המר מחרוזות רשימה לרשימות אמיתיות אם צריך
        self._parse_list_fields()

    def _parse_list_fields(self) -> None:
        """
        המרת שדות מסוג מחרוזת המייצגות רשימות לרשימות אמיתיות.
        תומך במחרוזות מופרדות בפסיק וב-JSON.
        """
        fields_to_check = [
            "ALLOWED_FILE_TYPES",
            "CORS_ORIGINS",
            "CORS_METHODS",
            "CORS_HEADERS",
            "ALLOWED_HOSTS",
            "EQUIPMENT_STATUS",
            "EQUIPMENT_TYPES",
            "PROJECT_STATUS",
            "PROJECT_PRIORITIES",
            "REPORT_TYPES",
            "REPORT_FORMATS",
        ]

        for field in fields_to_check:
            if hasattr(self, field):
                value = getattr(self, field)

                # אם זו כבר רשימה - אין צורך להמיר
                if isinstance(value, (list, set, tuple)):
                    continue

                # אם זו מחרוזת ריקה - המר לרשימה ריקה
                if value == "" or value is None:
                    setattr(self, field, [])
                    continue

                # ניסיון לפרש כ-JSON
                if isinstance(value, str):
                    try:
                        # בדיקה אם נראה כמו JSON
                        if (value.startswith("[") and value.endswith("]")) or (
                                value.startswith("{") and value.endswith("}")
                        ):
                            parsed_value = json.loads(value)
                            if isinstance(parsed_value, list):
                                setattr(self, field, parsed_value)
                                continue
                    except json.JSONDecodeError:
                        pass

                    # ניסיון לפרש כרשימה מופרדת בפסיקים
                    if "," in value:
                        items = [
                            item.strip() for item in value.split(",") if item.strip()
                        ]
                        setattr(self, field, items)
                    else:
                        # אם יש רק ערך אחד
                        setattr(self, field, [value])

    @property
    def redis_url(self) -> Optional[str]:
        """יצירת כתובת Redis מלאה"""
        if not self.REDIS_HOST:
            return None

        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        scheme = "rediss" if self.REDIS_SSL else "redis"
        return f"{scheme}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def is_production(self) -> bool:
        """בדיקה האם המערכת בסביבת ייצור"""
        return self.ENVIRONMENT.lower() == "production"

    def is_development(self) -> bool:
        """בדיקה האם המערכת בסביבת פיתוח"""
        return self.ENVIRONMENT.lower() == "development"

    def is_testing(self) -> bool:
        """בדיקה האם המערכת בסביבת בדיקות"""
        return self.ENVIRONMENT.lower() == "testing" or self.TESTING

    def get_email_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות אימייל"""
        return {
            "host": self.SMTP_HOST,
            "port": self.SMTP_PORT,
            "user": self.SMTP_USER,
            "password": self.SMTP_PASSWORD,
            "use_tls": self.SMTP_USE_TLS,
            "timeout": self.SMTP_TIMEOUT,
            "from_email": self.EMAIL_FROM,
            "from_name": self.EMAIL_FROM_NAME,
        }

    def get_file_upload_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות העלאת קבצים"""
        return {
            "upload_dir": self.UPLOAD_DIR,
            "max_size": self.MAX_FILE_SIZE,
            "allowed_types": self.ALLOWED_FILE_TYPES,
        }

    def get_db_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות מסד נתונים"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "echo": self.DB_ECHO,
        }

    def get_test_db_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות מסד נתונים לבדיקות"""
        return {
            "url": self.TEST_DATABASE_URL,
            "pool_size": self.TEST_DB_POOL_SIZE,
            "max_overflow": self.TEST_DB_MAX_OVERFLOW,
            "echo": self.DB_ECHO,
        }

    def get_token_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות טוקנים"""
        return {
            "secret_key": self.SECRET_KEY,
            "algorithm": self.ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.REFRESH_TOKEN_EXPIRE_DAYS,
            "password_reset_token_expire_hours": self.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
        }

    def get_redis_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות Redis"""
        return {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "password": self.REDIS_PASSWORD,
            "ssl": self.REDIS_SSL,
            "decode_responses": True,
        }

    def get_cors_settings(self) -> Dict[str, Any]:
        """קבלת הגדרות CORS"""
        return {
            "origins": list(self.CORS_ORIGINS),  # המרה מפורשת ל-list
            "methods": list(self.CORS_METHODS),  # המרה מפורשת ל-list
            "headers": list(self.CORS_HEADERS),  # המרה מפורשת ל-list
            "max_age": self.CORS_MAX_AGE,
            "credentials": True,
        }

    def get_db_uri(self, testing: bool = False) -> str:
        """
        מחזיר את כתובת ה-URI של מסד הנתונים

        Args:
            testing (bool): האם להשתמש במסד נתונים לבדיקות

        Returns:
            str: כתובת ה-URI המלאה למסד הנתונים
        """
        if testing or self.TESTING:
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL

    def validate_settings(self) -> None:
        """בדיקת תקינות ההגדרות"""
        errors = []

        # בדיקת הגדרות חובה
        if not self.DATABASE_URL and not self.is_testing():
            errors.append("DATABASE_URL is required")

        if not self.SECRET_KEY:
            errors.append("SECRET_KEY is required - generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        elif len(self.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")

        # בדיקות פרודקשן מחמירות
        if self.is_production():
            if self.DEBUG:
                errors.append("⚠️ CRITICAL: DEBUG must be False in production!")
            
            if "*" in self.CORS_ORIGINS or "localhost" in str(self.CORS_ORIGINS):
                errors.append("⚠️ CRITICAL: CORS_ORIGINS should not contain '*' or 'localhost' in production")
            
            if not self.SMTP_USER or not self.SMTP_PASSWORD:
                errors.append("⚠️ WARNING: SMTP credentials not configured")
            
            if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
                errors.append("⚠️ WARNING: DATABASE_URL should not use localhost in production")

        if errors:
            raise ValueError(f"Configuration errors:\n  - " + "\n  - ".join(errors))

    def setup_logging(self) -> None:
        """הגדרת מערכת הלוגים"""
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)

        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": self.LOG_FORMAT, "datefmt": self.LOG_DATE_FORMAT},
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s",
                    "datefmt": self.LOG_DATE_FORMAT,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": log_level,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": log_level,
            },
            "loggers": {
                "app": {"level": log_level},
                "sqlalchemy.engine": {
                    "level": logging.WARNING if not self.DB_ECHO else logging.INFO
                },
                "uvicorn": {"level": logging.INFO},
                "fastapi": {"level": log_level},
            },
        }

        # אם יש תיקיית לוגים, הוסף handler לקובץ
        logs_dir = Path("logs")
        try:
            logs_dir.mkdir(exist_ok=True)
            log_file = logs_dir / f"{self.ENVIRONMENT.lower()}.log"
            logging_config["handlers"]["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "filename": str(log_file),
                "maxBytes": self.LOG_FILE_MAX_BYTES,
                "backupCount": self.LOG_FILE_BACKUP_COUNT,
                "level": log_level,
            }
            # התיקון - עדכון הרשימה בצורה נכונה
            logging_config["root"]["handlers"] = ["console", "file"]
        except OSError:
            # אם לא מצליחים ליצור תיקיית logs, המשך בלי קובץ log
            pass

        logging.config.dictConfig(logging_config)

    # ==========================================
    # Properties for JWT compatibility
    # ==========================================
    @property
    def jwt_algorithm(self) -> str:
        """JWT Algorithm - alias for ALGORITHM"""
        return self.ALGORITHM

    @property
    def jwt_expiration_minutes(self) -> int:
        """JWT Expiration - alias for ACCESS_TOKEN_EXPIRE_MINUTES"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def jwt_refresh_expiration_days(self) -> int:
        """JWT Refresh Expiration - alias for REFRESH_TOKEN_EXPIRE_DAYS"""
        return self.REFRESH_TOKEN_EXPIRE_DAYS

    # Uppercase aliases for backward compatibility
    @property
    def JWT_ALGORITHM(self) -> str:
        """JWT Algorithm - uppercase alias for compatibility"""
        return self.ALGORITHM

    @property
    def JWT_EXPIRATION_MINUTES(self) -> int:
        """JWT Expiration - uppercase alias for compatibility"""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def JWT_REFRESH_EXPIRATION_DAYS(self) -> int:
        """JWT Refresh Expiration - uppercase alias for compatibility"""
        return self.REFRESH_TOKEN_EXPIRE_DAYS


# יצירת מופע סינגלטון של הגדרות
settings = Settings()

# אתחול לוגינג
settings.setup_logging()

# בדיקת תקינות הגדרות בסביבת פרודקשן
logger = logging.getLogger(__name__)
try:
    settings.validate_settings()
    logger.info("Settings validated successfully")
except ValueError as e:
    logger.error(f"Configuration validation failed: {e}")
    # בסביבת פיתוח - רק אזהרה, בפרודקשן - עצור
    if settings.is_production():
        raise
