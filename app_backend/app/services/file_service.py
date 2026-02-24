# app/services/file_service.py
"""File management service for uploads and documents."""
import hashlib
import mimetypes
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileCreate, FileUpdate


class FileService:
    """Service for file operations."""

    def __init__(self):
        # Create upload directories
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        for subdir in ["documents", "images", "reports", "temp"]:
            (self.upload_dir / subdir).mkdir(exist_ok=True)

    def get_file(self, db: Session, file_id: int) -> Optional[File]:
        """Get file by ID."""
        return (
            db.query(File)
            .filter(and_(File.id == file_id, File.is_active == True))
            .first()
        )

    def get_file_by_hash(self, db: Session, file_hash: str) -> Optional[File]:
        """Get file by hash (for deduplication)."""
        return (
            db.query(File)
            .filter(and_(File.file_hash == file_hash, File.is_active == True))
            .first()
        )

    def get_files(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        uploaded_by: Optional[int] = None,
        file_type: Optional[str] = None,
    ) -> List[File]:
        """Get list of files with filters."""
        query = db.query(File).filter(File.is_active == True)

        if entity_type:
            query = query.filter(File.entity_type == entity_type)
        if entity_id:
            query = query.filter(File.entity_id == entity_id)
        if uploaded_by:
            query = query.filter(File.uploaded_by_id == uploaded_by)
        if file_type:
            query = query.filter(File.mime_type.like(f"{file_type}%"))

        return query.order_by(File.uploaded_at.desc()).offset(skip).limit(limit).all()

    def upload_file(
        self,
        db: Session,
        file: BinaryIO,
        filename: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        uploaded_by_id: int = None,
        description: Optional[str] = None,
        is_public: bool = False,
    ) -> File:
        """Upload file and create database record."""
        # Read file content
        content = file.read()
        file_size = len(content)

        # Calculate hash for deduplication
        file_hash = hashlib.sha256(content).hexdigest()

        # Check if file already exists
        existing = self.get_file_by_hash(db, file_hash)
        if existing:
            # Just create a new reference to existing file
            return self._create_file_reference(
                db,
                existing_file=existing,
                entity_type=entity_type,
                entity_id=entity_id,
                uploaded_by_id=uploaded_by_id,
                description=description,
            )

        # Determine file type and directory
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        file_extension = Path(filename).suffix

        if mime_type.startswith("image"):
            subdir = "images"
        elif mime_type == "application/pdf" or file_extension == ".pdf":
            subdir = "documents"
        elif file_extension in [".xlsx", ".xls", ".csv"]:
            subdir = "reports"
        else:
            subdir = "documents"

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file_hash[:8]}{file_extension}"
        file_path = self.upload_dir / subdir / safe_filename

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)

        # Create database record
        db_file = File(
            original_name=filename,
            stored_name=safe_filename,
            file_path=str(file_path.relative_to(self.upload_dir)),
            file_size=file_size,
            file_hash=file_hash,
            mime_type=mime_type,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by_id=uploaded_by_id,
            description=description,
            is_public=is_public,
            uploaded_at=datetime.utcnow(),
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    def download_file(
        self, db: Session, file_id: int, user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Get file for download."""
        file_record = self.get_file(db, file_id)
        if not file_record:
            return None

        # Check access permissions
        if not file_record.is_public and user_id:
            # Check if user has access to the entity
            # TODO: Implement entity-specific access checks
            pass

        # Update download count
        file_record.download_count = (file_record.download_count or 0) + 1
        file_record.last_accessed_at = datetime.utcnow()
        db.commit()

        # Get file path
        file_path = self.upload_dir / file_record.file_path

        if not file_path.exists():
            return None

        return {
            "path": str(file_path),
            "filename": file_record.original_name,
            "mime_type": file_record.mime_type,
            "size": file_record.file_size,
        }

    def delete_file(self, db: Session, file_id: int, soft_delete: bool = True) -> bool:
        """Delete file (soft or hard delete)."""
        file_record = self.get_file(db, file_id)
        if not file_record:
            return False

        if soft_delete:
            # Soft delete - just mark as inactive
            file_record.is_active = False
            file_record.deleted_at = datetime.utcnow()
            db.commit()
        else:
            # Hard delete - remove file and record
            file_path = self.upload_dir / file_record.file_path

            # Check if other records use the same file
            other_refs = (
                db.query(File)
                .filter(
                    and_(
                        File.file_hash == file_record.file_hash,
                        File.id != file_id,
                        File.is_active == True,
                    )
                )
                .count()
            )

            # Only delete physical file if no other references
            if other_refs == 0 and file_path.exists():
                file_path.unlink()

            db.delete(file_record)
            db.commit()

        return True

    def get_entity_files(
        self, db: Session, entity_type: str, entity_id: int
    ) -> List[File]:
        """Get all files for an entity."""
        return (
            db.query(File)
            .filter(
                and_(
                    File.entity_type == entity_type,
                    File.entity_id == entity_id,
                    File.is_active == True,
                )
            )
            .order_by(File.uploaded_at.desc())
            .all()
        )

    def copy_file(
        self,
        db: Session,
        file_id: int,
        new_entity_type: str,
        new_entity_id: int,
        copied_by_id: int,
    ) -> Optional[File]:
        """Copy file reference to another entity."""
        original = self.get_file(db, file_id)
        if not original:
            return None

        # Create new file reference
        db_file = File(
            original_name=original.original_name,
            stored_name=original.stored_name,
            file_path=original.file_path,
            file_size=original.file_size,
            file_hash=original.file_hash,
            mime_type=original.mime_type,
            entity_type=new_entity_type,
            entity_id=new_entity_id,
            uploaded_by_id=copied_by_id,
            description=f"Copied from {original.entity_type}:{original.entity_id}",
            is_public=original.is_public,
            uploaded_at=datetime.utcnow(),
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file

    def get_storage_statistics(self, db: Session) -> Dict[str, Any]:
        """Get file storage statistics."""
        # Total files and size
        total_stats = (
            db.query(func.count(File.id), func.sum(File.file_size))
            .filter(File.is_active == True)
            .first()
        )

        total_files = total_stats[0] or 0
        total_size = total_stats[1] or 0

        # By type
        type_stats = (
            db.query(File.mime_type, func.count(File.id), func.sum(File.file_size))
            .filter(File.is_active == True)
            .group_by(File.mime_type)
            .all()
        )

        # By entity type
        entity_stats = (
            db.query(File.entity_type, func.count(File.id), func.sum(File.file_size))
            .filter(and_(File.is_active == True, File.entity_type != None))
            .group_by(File.entity_type)
            .all()
        )

        # Recent uploads
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_count = (
            db.query(func.count(File.id))
            .filter(and_(File.uploaded_at >= recent_cutoff, File.is_active == True))
            .scalar()
            or 0
        )

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
            "by_type": [
                {"type": t[0], "count": t[1], "size_bytes": t[2]} for t in type_stats
            ],
            "by_entity": [
                {"entity": e[0], "count": e[1], "size_bytes": e[2]}
                for e in entity_stats
            ],
            "recent_uploads_30d": recent_count,
        }

    def cleanup_temp_files(self, db: Session, days_old: int = 7) -> int:
        """Clean up old temporary files."""
        cutoff = datetime.utcnow() - timedelta(days=days_old)

        # Find old temp files
        old_files = (
            db.query(File)
            .filter(
                and_(
                    File.entity_type == "temp",
                    File.uploaded_at < cutoff,
                    File.is_active == True,
                )
            )
            .all()
        )

        count = 0
        for file in old_files:
            if self.delete_file(db, file.id, soft_delete=False):
                count += 1

        # Also clean physical temp directory
        temp_dir = self.upload_dir / "temp"
        for file_path in temp_dir.glob("*"):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff:
                    file_path.unlink()
                    count += 1

        return count

    def _create_file_reference(
        self,
        db: Session,
        existing_file: File,
        entity_type: Optional[str],
        entity_id: Optional[int],
        uploaded_by_id: int,
        description: Optional[str],
    ) -> File:
        """Create new reference to existing file."""
        db_file = File(
            original_name=existing_file.original_name,
            stored_name=existing_file.stored_name,
            file_path=existing_file.file_path,
            file_size=existing_file.file_size,
            file_hash=existing_file.file_hash,
            mime_type=existing_file.mime_type,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by_id=uploaded_by_id,
            description=description or f"Reference to {existing_file.original_name}",
            is_public=False,
            uploaded_at=datetime.utcnow(),
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file
