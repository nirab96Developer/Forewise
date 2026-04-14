# /root/app_backend/app/schemas/file.py - חדש
"""File schemas - Aligned with database model."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FileType(str, Enum):
    """File type enum - matches model."""

    IMAGE = "image"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    OTHER = "other"


class FileStatus(str, Enum):
    """File status enum - matches model."""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class FileBase(BaseModel):
    """Base file schema."""

    filename: str = Field(
        ..., min_length=1, max_length=255, description="Stored filename"
    )
    original_filename: str = Field(
        ..., min_length=1, max_length=255, description="Original filename"
    )

    # Type and format
    file_type: FileType = Field(..., description="File type")
    mime_type: str = Field(..., min_length=1, max_length=100, description="MIME type")

    # Additional info
    description: Optional[str] = Field(None, description="File description")
    tags: Optional[List[str]] = Field(None, description="File tags")


class FileCreate(BaseModel):
    """Create file schema - minimal fields for upload."""

    original_filename: str = Field(..., min_length=1, max_length=255)
    file_type: FileType
    mime_type: str = Field(..., min_length=1, max_length=100)
    file_size: int = Field(..., gt=0, description="File size in bytes")
    uploaded_by_id: int = Field(..., gt=0)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    checksum: Optional[str] = Field(None, max_length=64)


class FileUpdate(BaseModel):
    """Update file schema."""

    description: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metadata_json: Optional[Dict[str, Any]] = None
    status: Optional[FileStatus] = None
    is_active: Optional[bool] = None


class FileResponse(FileBase):
    """File response schema."""

    id: int

    # Size and location
    file_size: int
    file_path: str
    file_url: Optional[str] = None

    # Status
    status: FileStatus

    # Uploader
    uploaded_by_id: int

    # Additional
    custom_metadata_json: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Computed properties
    file_size_mb: float = 0.0
    file_size_kb: float = 0.0
    is_image: bool = False
    is_document: bool = False
    is_ready: bool = False

    # From relationships
    uploaded_by_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        """Calculate computed fields."""
        self.file_size_mb = self.file_size / (1024 * 1024)
        self.file_size_kb = self.file_size / 1024
        self.is_image = self.file_type == FileType.IMAGE
        self.is_document = self.file_type in [
            FileType.DOCUMENT,
            FileType.PDF,
            FileType.SPREADSHEET,
        ]
        self.is_ready = self.status == FileStatus.READY


class FileFilter(BaseModel):
    """Filter for files."""

    search: Optional[str] = Field(
        None, description="Search in filename, original_filename"
    )
    file_type: Optional[FileType] = None
    file_types: Optional[List[FileType]] = None
    mime_type: Optional[str] = None
    status: Optional[FileStatus] = None
    statuses: Optional[List[FileStatus]] = None
    uploaded_by_id: Optional[int] = None
    min_size: Optional[int] = Field(None, description="Minimum file size in bytes")
    max_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    tags: Optional[List[str]] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class FileStatistics(BaseModel):
    """File statistics."""

    total_files: int = 0
    total_size_bytes: int = 0
    total_size_mb: float = 0.0
    total_size_gb: float = 0.0

    # By type
    by_type: Dict[str, int] = Field(default_factory=dict)

    # By status
    by_status: Dict[str, int] = Field(default_factory=dict)

    # Size distribution
    small_files: int = 0  # < 1MB
    medium_files: int = 0  # 1MB - 10MB
    large_files: int = 0  # > 10MB

    # Recent uploads
    uploads_today: int = 0
    uploads_this_week: int = 0
    uploads_this_month: int = 0


class FileUploadResponse(BaseModel):
    """Response after file upload."""

    file_id: int
    filename: str
    original_filename: str
    file_url: Optional[str]
    file_size: int
    file_type: FileType
    status: FileStatus
    message: str = "File uploaded successfully"


class FileShare(BaseModel):
    """File sharing schema."""

    file_id: int = Field(..., gt=0, description="File ID to share")
    shared_with_user_id: int = Field(..., gt=0, description="User ID to share with")
    permission: str = Field("read", description="Permission level: read, write, admin")
    expires_at: Optional[datetime] = Field(None, description="Share expiration date")
    message: Optional[str] = Field(None, max_length=500, description="Share message")


class FolderCreate(BaseModel):
    """Folder creation schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Folder name")
    parent_folder_id: Optional[int] = Field(None, gt=0, description="Parent folder ID")
    description: Optional[str] = Field(None, max_length=500, description="Folder description")
    is_public: bool = Field(False, description="Is folder public")


class FolderResponse(BaseModel):
    """Folder response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_folder_id: Optional[int] = None
    description: Optional[str] = None
    is_public: bool
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # From relationships
    created_by_name: Optional[str] = None
    parent_folder_name: Optional[str] = None
    file_count: int = 0
    subfolder_count: int = 0