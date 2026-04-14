# app/utils/common.py
"""
Common utility functions used throughout the application
"""

import base64
import hashlib
import json
import os
import random
import re
import string
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from app.core.logging import logger


def generate_unique_id(length: int = 8) -> str:
    """
    Generate a unique random string ID.

    Args:
        length: Length of the ID

    Returns:
        Random string ID
    """
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token

    Returns:
        Secure random token
    """
    return base64.urlsafe_b64encode(os.urandom(length))[:length].decode("utf-8")


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm.

    Args:
        value: String to hash
        algorithm: Hash algorithm (sha256, sha512, md5)

    Returns:
        Hex digest of hash
    """
    h = hashlib.new(algorithm)
    h.update(value.encode("utf-8"))
    return h.hexdigest()


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be safe for filesystem.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators and null bytes
    filename = filename.replace("/", "_").replace("\\", "_").replace("\0", "_")

    # Remove other potentially problematic characters
    filename = re.sub(r'[<>:"|?*]', "_", filename)

    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]

    return name + ext


def parse_bool(value: Any) -> bool:
    """
    Parse various representations of boolean values.

    Args:
        value: Value to parse

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "y", "t", "on")

    return bool(value)


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: Base dictionary
        dict2: Dictionary to merge in

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def format_bytes(size: int) -> str:
    """
    Format byte size to human readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0

    return f"{size:.2f} PB"


def calculate_checksum(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """
    Calculate checksum of data.

    Args:
        data: Data to checksum
        algorithm: Hash algorithm

    Returns:
        Hex digest checksum
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON with error handling.

    Args:
        json_str: JSON string
        default: Default value if parsing fails

    Returns:
        Parsed value or default
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON: {json_str[:100]}...")
        return default


def extract_extension(filename: str) -> str:
    """
    Extract file extension safely.

    Args:
        filename: Filename

    Returns:
        Extension without dot or empty string
    """
    if not filename or "." not in filename:
        return ""

    return filename.rsplit(".", 1)[1].lower()


def generate_slug(text: str) -> str:
    """
    Generate URL-safe slug from text.

    Args:
        text: Text to slugify

    Returns:
        URL-safe slug
    """
    # Convert to lowercase and replace spaces
    slug = text.lower().strip()
    slug = re.sub(r"\s+", "-", slug)

    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r"[^a-z0-9\-]", "", slug)

    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    return slug


def is_valid_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address

    Returns:
        True if valid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_uuid(value: str) -> bool:
    """
    Check if string is valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def parse_datetime(value: Union[str, datetime, date]) -> Optional[datetime]:
    """
    Parse various datetime formats.

    Args:
        value: Value to parse

    Returns:
        datetime object or None
    """
    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())

    if isinstance(value, str):
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        # Try ISO format
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except:
            pass

    return None
