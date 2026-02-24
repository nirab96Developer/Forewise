# app/utils/files/storage.py
"""
File storage service with multiple provider support

Supports local filesystem, S3, Azure Blob Storage, and Google Cloud Storage
with metadata management, file operations, and provider abstraction.
"""

import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import (IO, Any, AsyncGenerator, BinaryIO, Dict, List, Optional,
                    Tuple, Union)

import aiofiles
import aiofiles.os

# External providers
try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_S3 = True
except ImportError:
    HAS_S3 = False

try:
    from azure.storage.blob import BlobServiceClient

    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

try:
    from google.cloud import storage as gcs

    HAS_GCS = True
except ImportError:
    HAS_GCS = False

from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import logger
from app.utils.common import ensure_directory, generate_unique_id


class StorageProvider(str, Enum):
    """Supported storage providers"""

    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class FileCategory(str, Enum):
    """File categories for organization"""

    PROFILE_IMAGE = "profile_image"
    ATTACHMENT = "attachment"
    DOCUMENT = "document"
    EXPORT = "export"
    REPORT = "report"
    BACKUP = "backup"
    TEMP = "temp"
    ARCHIVE = "archive"
    MEDIA = "media"
    OTHER = "other"


class FileMetadata:
    """File metadata model"""

    def __init__(
        self,
        filename: str,
        size: int,
        content_type: str,
        category: FileCategory = FileCategory.OTHER,
        owner_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ):
        self.filename = filename
        self.size = size
        self.content_type = content_type
        self.category = category
        self.owner_id = owner_id
        self.tags = tags or []
        self.custom_data = custom_data or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.checksum: Optional[str] = None
        self.version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "filename": self.filename,
            "size": self.size,
            "content_type": self.content_type,
            "category": self.category.value,
            "owner_id": self.owner_id,
            "tags": self.tags,
            "custom_data": self.custom_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "checksum": self.checksum,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        """Create from dictionary"""
        metadata = cls(
            filename=data["filename"],
            size=data["size"],
            content_type=data["content_type"],
            category=FileCategory(data.get("category", FileCategory.OTHER.value)),
            owner_id=data.get("owner_id"),
            tags=data.get("tags", []),
            custom_data=data.get("custom_data", {}),
        )

        if "created_at" in data:
            metadata.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            metadata.updated_at = datetime.fromisoformat(data["updated_at"])
        if "checksum" in data:
            metadata.checksum = data["checksum"]
        if "version" in data:
            metadata.version = data["version"]

        return metadata


class StorageService:
    """
    Unified file storage service

    Provides abstraction over multiple storage providers with
    consistent API for file operations, metadata management,
    and advanced features like versioning and migration.
    """

    def __init__(self, provider: Optional[StorageProvider] = None):
        """
        Initialize storage service

        Args:
            provider: Storage provider (defaults to settings)
        """
        self.provider = provider or StorageProvider(settings.STORAGE_PROVIDER)

        # Initialize provider-specific settings
        if self.provider == StorageProvider.LOCAL:
            self.local_path = Path(settings.STORAGE_LOCAL_PATH)
            ensure_directory(self.local_path)

            # Create category directories
            for category in FileCategory:
                category_path = self.local_path / category.value
                ensure_directory(category_path)

        elif self.provider == StorageProvider.S3:
            if not HAS_S3:
                raise ImportError(
                    "boto3 is required for S3 storage. Install with: pip install boto3"
                )

            self.s3_bucket = settings.S3_BUCKET_NAME
            self.s3_region = settings.AWS_DEFAULT_REGION
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.s3_region,
            )

        elif self.provider == StorageProvider.AZURE:
            if not HAS_AZURE:
                raise ImportError("azure-storage-blob is required for Azure storage")

            self.azure_connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
            self.azure_container = settings.AZURE_STORAGE_CONTAINER
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.azure_connection_string
            )

        elif self.provider == StorageProvider.GCS:
            if not HAS_GCS:
                raise ImportError("google-cloud-storage is required for GCS")

            self.gcs_bucket_name = settings.GCS_BUCKET_NAME
            self.gcs_client = gcs.Client()
            self.gcs_bucket = self.gcs_client.bucket(self.gcs_bucket_name)

        # Statistics
        self.stats = {
            "uploads": 0,
            "downloads": 0,
            "deletes": 0,
            "errors": 0,
            "bytes_uploaded": 0,
            "bytes_downloaded": 0,
        }

        logger.info(f"Storage service initialized with provider: {self.provider.value}")

    async def upload_file(
        self,
        file: Union[UploadFile, IO, bytes, str, Path],
        destination: Optional[str] = None,
        category: FileCategory = FileCategory.OTHER,
        metadata: Optional[FileMetadata] = None,
        overwrite: bool = False,
        compute_checksum: bool = True,
    ) -> Dict[str, Any]:
        """
        Upload file to storage

        Args:
            file: File to upload
            destination: Destination path (auto-generated if not provided)
            category: File category
            metadata: File metadata
            overwrite: Whether to overwrite existing files
            compute_checksum: Whether to compute file checksum

        Returns:
            Dict with file information
        """
        try:
            # Get file content and info
            content, filename, size = await self._prepare_file_content(file)

            # Generate destination if not provided
            if not destination:
                timestamp = datetime.utcnow().strftime("%Y/%m/%d")
                unique_id = generate_unique_id(8)
                extension = Path(filename).suffix if filename else ""
                destination = f"{category.value}/{timestamp}/{unique_id}{extension}"

            # Check if file exists
            if not overwrite and await self.file_exists(destination):
                raise FileExistsError(f"File already exists: {destination}")

            # Compute checksum if requested
            checksum = None
            if compute_checksum:
                checksum = hashlib.sha256(content).hexdigest()

            # Create or update metadata
            if not metadata:
                content_type, _ = (
                    mimetypes.guess_type(filename) if filename else (None, None)
                )
                metadata = FileMetadata(
                    filename=filename or "unknown",
                    size=size,
                    content_type=content_type or "application/octet-stream",
                    category=category,
                )

            metadata.checksum = checksum

            # Upload based on provider
            if self.provider == StorageProvider.LOCAL:
                result = await self._upload_local(content, destination, metadata)
            elif self.provider == StorageProvider.S3:
                result = await self._upload_s3(content, destination, metadata)
            elif self.provider == StorageProvider.AZURE:
                result = await self._upload_azure(content, destination, metadata)
            elif self.provider == StorageProvider.GCS:
                result = await self._upload_gcs(content, destination, metadata)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Update statistics
            self.stats["uploads"] += 1
            self.stats["bytes_uploaded"] += size

            logger.info(f"File uploaded successfully: {destination}")
            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"File upload failed: {str(e)}")
            raise

    async def download_file(
        self, file_path: str, stream: bool = False
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """
        Download file from storage

        Args:
            file_path: File path
            stream: Whether to stream the file

        Returns:
            File content or async generator for streaming
        """
        try:
            if self.provider == StorageProvider.LOCAL:
                result = await self._download_local(file_path, stream)
            elif self.provider == StorageProvider.S3:
                result = await self._download_s3(file_path, stream)
            elif self.provider == StorageProvider.AZURE:
                result = await self._download_azure(file_path, stream)
            elif self.provider == StorageProvider.GCS:
                result = await self._download_gcs(file_path, stream)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Update statistics (only for non-streaming downloads)
            if not stream and result:
                self.stats["downloads"] += 1
                self.stats["bytes_downloaded"] += len(result)

            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"File download failed: {str(e)}")
            raise

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage

        Args:
            file_path: File path

        Returns:
            Whether deletion was successful
        """
        try:
            if self.provider == StorageProvider.LOCAL:
                result = await self._delete_local(file_path)
            elif self.provider == StorageProvider.S3:
                result = await self._delete_s3(file_path)
            elif self.provider == StorageProvider.AZURE:
                result = await self._delete_azure(file_path)
            elif self.provider == StorageProvider.GCS:
                result = await self._delete_gcs(file_path)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            if result:
                self.stats["deletes"] += 1
                logger.info(f"File deleted successfully: {file_path}")

            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"File deletion failed: {str(e)}")
            return False

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists

        Args:
            file_path: File path

        Returns:
            Whether file exists
        """
        try:
            if self.provider == StorageProvider.LOCAL:
                full_path = self.local_path / file_path
                return await aiofiles.os.path.exists(str(full_path))

            elif self.provider == StorageProvider.S3:
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: self.s3_client.head_object(
                            Bucket=self.s3_bucket, Key=file_path
                        ),
                    )
                    return True
                except ClientError:
                    return False

            # Add Azure and GCS implementations
            return False

        except Exception:
            return False

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information including metadata

        Args:
            file_path: File path

        Returns:
            File information or None if not found
        """
        try:
            if self.provider == StorageProvider.LOCAL:
                return await self._get_local_file_info(file_path)
            elif self.provider == StorageProvider.S3:
                return await self._get_s3_file_info(file_path)
            # Add other providers

            return None

        except Exception as e:
            logger.error(f"Failed to get file info: {str(e)}")
            return None

    async def list_files(
        self,
        prefix: str = "",
        category: Optional[FileCategory] = None,
        limit: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List files in storage

        Args:
            prefix: Path prefix to filter files
            category: Category to filter by
            limit: Maximum number of files to return
            continuation_token: Token for pagination

        Returns:
            Dict with files list and continuation token
        """
        try:
            # Add category to prefix if specified
            if category:
                prefix = f"{category.value}/{prefix}".strip("/")

            if self.provider == StorageProvider.LOCAL:
                return await self._list_local_files(prefix, limit, continuation_token)
            elif self.provider == StorageProvider.S3:
                return await self._list_s3_files(prefix, limit, continuation_token)
            # Add other providers

            return {"files": [], "continuation_token": None}

        except Exception as e:
            logger.error(f"Failed to list files: {str(e)}")
            return {"files": [], "continuation_token": None}

    async def copy_file(
        self, source_path: str, destination_path: str, overwrite: bool = False
    ) -> bool:
        """
        Copy file within storage

        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file

        Returns:
            Whether copy was successful
        """
        try:
            # Check if destination exists
            if not overwrite and await self.file_exists(destination_path):
                raise FileExistsError(
                    f"Destination file already exists: {destination_path}"
                )

            # Download and re-upload
            content = await self.download_file(source_path)
            metadata = await self.get_file_metadata(source_path)

            await self.upload_file(
                file=content,
                destination=destination_path,
                metadata=metadata,
                overwrite=overwrite,
            )

            logger.info(f"File copied: {source_path} -> {destination_path}")
            return True

        except Exception as e:
            logger.error(f"File copy failed: {str(e)}")
            return False

    async def move_file(
        self, source_path: str, destination_path: str, overwrite: bool = False
    ) -> bool:
        """
        Move file within storage

        Args:
            source_path: Source file path
            destination_path: Destination file path
            overwrite: Whether to overwrite existing file

        Returns:
            Whether move was successful
        """
        try:
            # Copy file
            if await self.copy_file(source_path, destination_path, overwrite):
                # Delete source
                return await self.delete_file(source_path)

            return False

        except Exception as e:
            logger.error(f"File move failed: {str(e)}")
            return False

    async def get_file_url(
        self, file_path: str, expires_in: int = 3600, download: bool = False
    ) -> Optional[str]:
        """
        Get temporary URL for file access

        Args:
            file_path: File path
            expires_in: URL expiration time in seconds
            download: Whether to force download

        Returns:
            Temporary URL or None
        """
        try:
            if self.provider == StorageProvider.LOCAL:
                # Return relative URL for local files
                return f"/api/v1/files/download/{file_path}"

            elif self.provider == StorageProvider.S3:
                params = {"Bucket": self.s3_bucket, "Key": file_path}

                if download:
                    filename = Path(file_path).name
                    params[
                        "ResponseContentDisposition"
                    ] = f'attachment; filename="{filename}"'

                loop = asyncio.get_event_loop()
                url = await loop.run_in_executor(
                    None,
                    lambda: self.s3_client.generate_presigned_url(
                        "get_object", Params=params, ExpiresIn=expires_in
                    ),
                )
                return url

            # Add other providers
            return None

        except Exception as e:
            logger.error(f"Failed to generate file URL: {str(e)}")
            return None

    async def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """
        Get file metadata

        Args:
            file_path: File path

        Returns:
            File metadata or None
        """
        try:
            info = await self.get_file_info(file_path)
            if info and "metadata" in info:
                return FileMetadata.from_dict(info["metadata"])
            return None

        except Exception:
            return None

    async def update_file_metadata(
        self, file_path: str, metadata: FileMetadata
    ) -> bool:
        """
        Update file metadata

        Args:
            file_path: File path
            metadata: New metadata

        Returns:
            Whether update was successful
        """
        try:
            metadata.updated_at = datetime.utcnow()
            metadata.version += 1

            if self.provider == StorageProvider.LOCAL:
                return await self._update_local_metadata(file_path, metadata)
            elif self.provider == StorageProvider.S3:
                return await self._update_s3_metadata(file_path, metadata)
            # Add other providers

            return False

        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
            return False

    async def cleanup_old_files(
        self,
        days: int = 30,
        category: Optional[FileCategory] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Clean up old files

        Args:
            days: Delete files older than this many days
            category: Limit to specific category
            dry_run: Whether to simulate without deleting

        Returns:
            Cleanup results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            results = {"scanned": 0, "deleted": 0, "errors": 0, "bytes_freed": 0}

            # List all files
            files_response = await self.list_files(category=category)
            files = files_response.get("files", [])

            for file_info in files:
                results["scanned"] += 1

                # Check file age
                created_at = file_info.get("created_at")
                if created_at:
                    file_date = datetime.fromisoformat(created_at)
                    if file_date < cutoff_date:
                        if not dry_run:
                            if await self.delete_file(file_info["path"]):
                                results["deleted"] += 1
                                results["bytes_freed"] += file_info.get("size", 0)
                            else:
                                results["errors"] += 1
                        else:
                            results["deleted"] += 1
                            results["bytes_freed"] += file_info.get("size", 0)

            logger.info(f"Cleanup completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            return {
                "scanned": 0,
                "deleted": 0,
                "errors": 1,
                "bytes_freed": 0,
                "error": str(e),
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "provider": self.provider.value,
            "stats": self.stats.copy(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    # Private helper methods

    async def _prepare_file_content(
        self, file: Union[UploadFile, IO, bytes, str, Path]
    ) -> Tuple[bytes, Optional[str], int]:
        """Prepare file content for upload"""
        if isinstance(file, UploadFile):
            content = await file.read()
            return content, file.filename, len(content)

        elif isinstance(file, bytes):
            return file, None, len(file)

        elif isinstance(file, (str, Path)):
            file_path = Path(file)
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            return content, file_path.name, len(content)

        else:  # IO object
            content = file.read()
            if isinstance(content, str):
                content = content.encode()
            filename = getattr(file, "name", None)
            return content, filename, len(content)

    # Provider-specific implementations

    async def _upload_local(
        self, content: bytes, destination: str, metadata: FileMetadata
    ) -> Dict[str, Any]:
        """Upload to local filesystem"""
        full_path = self.local_path / destination
        ensure_directory(full_path.parent)

        # Write file
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)

        # Write metadata
        meta_path = full_path.with_suffix(full_path.suffix + ".meta.json")
        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(metadata.to_dict(), indent=2))

        return {
            "path": destination,
            "size": len(content),
            "url": f"/api/v1/files/download/{destination}",
            "provider": self.provider.value,
        }

    async def _download_local(
        self, file_path: str, stream: bool = False
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """Download from local filesystem"""
        full_path = self.local_path / file_path

        if not await aiofiles.os.path.exists(str(full_path)):
            raise FileNotFoundError(f"File not found: {file_path}")

        if stream:

            async def file_generator():
                async with aiofiles.open(full_path, "rb") as f:
                    chunk_size = 8192
                    while True:
                        chunk = await f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk

            return file_generator()
        else:
            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()

    async def _delete_local(self, file_path: str) -> bool:
        """Delete from local filesystem"""
        full_path = self.local_path / file_path

        if await aiofiles.os.path.exists(str(full_path)):
            await aiofiles.os.remove(str(full_path))

            # Delete metadata if exists
            meta_path = full_path.with_suffix(full_path.suffix + ".meta.json")
            if await aiofiles.os.path.exists(str(meta_path)):
                await aiofiles.os.remove(str(meta_path))

            return True

        return False

    async def _get_local_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get local file information"""
        full_path = self.local_path / file_path

        if not await aiofiles.os.path.exists(str(full_path)):
            return None

        stat = await aiofiles.os.stat(str(full_path))

        # Read metadata if exists
        metadata = {}
        meta_path = full_path.with_suffix(full_path.suffix + ".meta.json")
        if await aiofiles.os.path.exists(str(meta_path)):
            async with aiofiles.open(meta_path, "r") as f:
                metadata = json.loads(await f.read())

        return {
            "path": file_path,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "metadata": metadata,
        }

    async def _list_local_files(
        self, prefix: str, limit: int, continuation_token: Optional[str]
    ) -> Dict[str, Any]:
        """List local files"""
        files = []
        base_path = self.local_path / prefix if prefix else self.local_path

        if not base_path.exists():
            return {"files": [], "continuation_token": None}

        # Get all files recursively
        all_files = []
        for file_path in base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith(".meta.json"):
                relative_path = file_path.relative_to(self.local_path)
                all_files.append(str(relative_path))

        # Sort for consistent pagination
        all_files.sort()

        # Apply pagination
        start_index = 0
        if continuation_token:
            try:
                start_index = int(continuation_token)
            except ValueError:
                pass

        end_index = min(start_index + limit, len(all_files))
        selected_files = all_files[start_index:end_index]

        # Get file info
        for file_path in selected_files:
            info = await self._get_local_file_info(file_path)
            if info:
                files.append(info)

        # Create continuation token
        next_token = None
        if end_index < len(all_files):
            next_token = str(end_index)

        return {"files": files, "continuation_token": next_token}

    async def _update_local_metadata(
        self, file_path: str, metadata: FileMetadata
    ) -> bool:
        """Update local file metadata"""
        full_path = self.local_path / file_path

        if not await aiofiles.os.path.exists(str(full_path)):
            return False

        meta_path = full_path.with_suffix(full_path.suffix + ".meta.json")
        async with aiofiles.open(meta_path, "w") as f:
            await f.write(json.dumps(metadata.to_dict(), indent=2))

        return True

    # S3-specific implementations

    async def _upload_s3(
        self, content: bytes, destination: str, metadata: FileMetadata
    ) -> Dict[str, Any]:
        """Upload to S3"""
        extra_args = {
            "ContentType": metadata.content_type,
            "Metadata": {
                f"x-amz-meta-{k}": str(v)
                for k, v in metadata.to_dict().items()
                if isinstance(v, (str, int, float, bool))
            },
        }

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.put_object(
                Bucket=self.s3_bucket, Key=destination, Body=content, **extra_args
            ),
        )

        return {
            "path": destination,
            "size": len(content),
            "url": await self.get_file_url(destination),
            "provider": self.provider.value,
        }

    async def _download_s3(
        self, file_path: str, stream: bool = False
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """Download from S3"""
        try:
            loop = asyncio.get_event_loop()

            if stream:
                # For streaming, we need to handle it differently
                # S3 doesn't support true async streaming, so we'll download in chunks
                async def s3_generator():
                    response = await loop.run_in_executor(
                        None,
                        lambda: self.s3_client.get_object(
                            Bucket=self.s3_bucket, Key=file_path
                        ),
                    )

                    body = response["Body"]
                    chunk_size = 8192

                    while True:
                        chunk = await loop.run_in_executor(None, body.read, chunk_size)
                        if not chunk:
                            break
                        yield chunk

                return s3_generator()
            else:
                response = await loop.run_in_executor(
                    None,
                    lambda: self.s3_client.get_object(
                        Bucket=self.s3_bucket, Key=file_path
                    ),
                )
                return response["Body"].read()

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {file_path}")
            raise

    async def _delete_s3(self, file_path: str) -> bool:
        """Delete from S3"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(
                    Bucket=self.s3_bucket, Key=file_path
                ),
            )
            return True
        except Exception:
            return False

    async def _get_s3_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get S3 file information"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(
                    Bucket=self.s3_bucket, Key=file_path
                ),
            )

            # Extract metadata
            metadata = {}
            for key, value in response.get("Metadata", {}).items():
                if key.startswith("x-amz-meta-"):
                    metadata[key[11:]] = value
                else:
                    metadata[key] = value

            return {
                "path": file_path,
                "size": response["ContentLength"],
                "created_at": response["LastModified"].isoformat(),
                "modified_at": response["LastModified"].isoformat(),
                "content_type": response.get("ContentType"),
                "etag": response.get("ETag"),
                "metadata": metadata,
            }
        except ClientError:
            return None

    async def _list_s3_files(
        self, prefix: str, limit: int, continuation_token: Optional[str]
    ) -> Dict[str, Any]:
        """List S3 files"""
        params = {"Bucket": self.s3_bucket, "MaxKeys": limit}

        if prefix:
            params["Prefix"] = prefix

        if continuation_token:
            params["ContinuationToken"] = continuation_token

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.s3_client.list_objects_v2(**params)
            )

            files = []
            for obj in response.get("Contents", []):
                # Get detailed info for each file
                info = await self._get_s3_file_info(obj["Key"])
                if info:
                    files.append(info)

            return {
                "files": files,
                "continuation_token": response.get("NextContinuationToken"),
            }
        except Exception:
            return {"files": [], "continuation_token": None}

    async def _update_s3_metadata(self, file_path: str, metadata: FileMetadata) -> bool:
        """Update S3 file metadata"""
        try:
            # S3 requires copying the object to update metadata
            loop = asyncio.get_event_loop()

            # Get current object info
            head_response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(
                    Bucket=self.s3_bucket, Key=file_path
                ),
            )

            # Copy with new metadata
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.copy_object(
                    Bucket=self.s3_bucket,
                    CopySource={"Bucket": self.s3_bucket, "Key": file_path},
                    Key=file_path,
                    ContentType=head_response.get(
                        "ContentType", "application/octet-stream"
                    ),
                    Metadata={
                        f"x-amz-meta-{k}": str(v)
                        for k, v in metadata.to_dict().items()
                        if isinstance(v, (str, int, float, bool))
                    },
                    MetadataDirective="REPLACE",
                ),
            )

            return True
        except Exception:
            return False

    # Placeholder implementations for Azure and GCS

    async def _upload_azure(
        self, content: bytes, destination: str, metadata: FileMetadata
    ) -> Dict[str, Any]:
        """Upload to Azure Blob Storage"""
        # TODO: Implement Azure upload
        raise NotImplementedError("Azure storage not yet implemented")

    async def _download_azure(
        self, file_path: str, stream: bool = False
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """Download from Azure Blob Storage"""
        # TODO: Implement Azure download
        raise NotImplementedError("Azure storage not yet implemented")

    async def _delete_azure(self, file_path: str) -> bool:
        """Delete from Azure Blob Storage"""
        # TODO: Implement Azure delete
        raise NotImplementedError("Azure storage not yet implemented")

    async def _upload_gcs(
        self, content: bytes, destination: str, metadata: FileMetadata
    ) -> Dict[str, Any]:
        """Upload to Google Cloud Storage"""
        # TODO: Implement GCS upload
        raise NotImplementedError("GCS storage not yet implemented")

    async def _download_gcs(
        self, file_path: str, stream: bool = False
    ) -> Union[bytes, AsyncGenerator[bytes, None]]:
        """Download from Google Cloud Storage"""
        # TODO: Implement GCS download
        raise NotImplementedError("GCS storage not yet implemented")

    async def _delete_gcs(self, file_path: str) -> bool:
        """Delete from Google Cloud Storage"""
        # TODO: Implement GCS delete
        raise NotImplementedError("GCS storage not yet implemented")


# Create singleton instance
storage_service = StorageService()
