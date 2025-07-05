"""
Enhanced file upload security utilities
"""
import os
import hashlib
import magic
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List
from datetime import datetime
import uuid
import re
from fastapi import UploadFile, HTTPException
import aiofiles
import logging

from core.config import settings
from core.exceptions import ValidationException

logger = logging.getLogger(__name__)


class FileSecurityValidator:
    """Secure file upload validation and processing"""

    # Safe文件extensions by category
    ALLOWED_EXTENSIONS = {
        "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
        "document": {".pdf", ".doc", ".docx", ".txt", ".md"},
        "spreadsheet": {".xls", ".xlsx", ".csv"},
        "presentation": {".ppt", ".pptx"},
        "video": {".mp4", ".avi", ".mov", ".webm"},
        "audio": {".mp3", ".wav", ".ogg", ".m4a"}
    }

    # MIME type mapping
    MIME_TYPES = {
        # Images
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
        "image/gif": [".gif"],
        "image/webp": [".webp"],
        # Documents
        "application/pdf": [".pdf"],
        "application/msword": [".doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
        "text/plain": [".txt"],
        "text/markdown": [".md"],
        # Spreadsheets
        "application/vnd.ms-excel": [".xls"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
        "text/csv": [".csv"],
        # Presentations
        "application/vnd.ms-powerpoint": [".ppt"],
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"]
    }

    # Maximum文件sizes by type (in bytes)
    MAX_FILE_SIZES = {
        "image": 5 * 1024 * 1024,  # 5MB
        "document": 10 * 1024 * 1024,  # 10MB
        "spreadsheet": 15 * 1024 * 1024,  # 15MB
        "presentation": 25 * 1024 * 1024,  # 25MB
        "video": 100 * 1024 * 1024,  # 100MB
        "audio": 20 * 1024 * 1024  # 20MB
    }

    # Dangerous patterns to检查in filenames
    DANGEROUS_PATTERNS = [
        r"\.\./",
        # 路径traversal
        r"\.\.$",
        # 路径traversal
        r"\.\.\\",
        # Windows路径traversal
        r"^/",
        # Absolute路径
        r"^\\",
        # Windows absolute路径
        r"[<>:|?*]",  # Invalid filename characters
        r"[\x00-\x1f]",  # Control characters
        r"^\..*",  # Hidden files
        r".*\$.*",  # Shell variables
        r".*`.*",
        # 命令substitution
    ]

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # 初始化magic for MIME type detection
        try:
            self.mime = magic.Magic(mime=True)
        except Exception as e:
            logger.warning(f"Failed to initialize magic library: {e}")
            self.mime = None

    def get_file_category(self, extension: str) -> Optional[str]:
        """Get file category from extension"""
        extension = extension.lower()
        for category, extensions in self.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return category
        return None

    def validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate filename for security issues"""
        # 检查空filename
        if not filename or filename.strip() == "":
            return False, "Empty filename"

        # 检查length
        if len(filename) > 255:
            return False, "Filename too long"

        # 检查dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, filename):
                return False, f"Dangerous pattern detected in filename"

        # 检查double extensions
        if filename.count('.') > 2:
            return False, "Multiple extensions detected"

        return True, None

    def validate_extension(self, filename: str,
                          allowed_categories: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """Validate file extension"""
        extension = Path(filename).suffix.lower()

        if not extension:
            return False, "No file extension"

        # 检查if extension is allowed
        if allowed_categories:
            # 检查specific categories
            allowed_extensions = set()
            for category in allowed_categories:
                allowed_extensions.update(self.ALLOWED_EXTENSIONS.get(category, set()))

            if extension not in allowed_extensions:
                return False, f"File type {extension} not allowed"
        else:
            # 检查全部categories
            all_extensions = set()
            for extensions in self.ALLOWED_EXTENSIONS.values():
                all_extensions.update(extensions)

            if extension not in all_extensions:
                return False, f"File type {extension} not allowed"

        return True, None

    def validate_mime_type(self, file_path: Path, expected_extension: str) -> Tuple[bool, Optional[str]]:
        """Validate MIME type matches extension"""
        if not self.mime or not file_path.exists():
            return True, None
            # Skip验证if magic not available

        try:
            detected_mime = self.mime.from_file(str(file_path))

            # 检查if MIME type is in our whitelist
            if detected_mime not in self.MIME_TYPES:
                return False, f"Unknown MIME type: {detected_mime}"

            # 检查if extension matches MIME type
            expected_extensions = self.MIME_TYPES.get(detected_mime, [])
            if expected_extension not in expected_extensions:
                return False, f"Extension {expected_extension} doesn't match MIME type {detected_mime}"

            return True, None

        except Exception as e:
            logger.error(f"MIME type validation error: {e}")
            return True, None  # Don't block on errors

    def validate_file_size(self, file_size: int, file_category: str) -> Tuple[bool, Optional[str]]:
        """Validate file size"""
        max_size = self.MAX_FILE_SIZES.get(file_category, settings.max_upload_size)

        if file_size > max_size:
            return False, f"File too large. Maximum size is {max_size // (1024*1024)}MB"

        if file_size == 0:
            return False, "Empty file"

        return True, None

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # 获取base name and extension
        base_name = Path(filename).stem
        extension = Path(filename).suffix.lower()

        # Remove special characters
        base_name = re.sub(r'[^\w\s-]', '', base_name)
        base_name = re.sub(r'[-\s]+', '-', base_name)

        # 限制length
        if len(base_name) > 100:
            base_name = base_name[:100]

        # 生成唯一filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        return f"{base_name}_{timestamp}_{unique_id}{extension}"

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate file hash for integrity checking"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    async def save_upload_file(
        self,
        upload_file: UploadFile,
        allowed_categories: Optional[List[str]] = None,
        subfolder: Optional[str] = None
    ) -> Tuple[str, dict]:
        """Safely save an uploaded file"""

        # 校验filename
        valid, error = self.validate_filename(upload_file.filename)
        if not valid:
            raise ValidationException(f"Invalid filename: {error}")

        # 校验extension
        valid, error = self.validate_extension(upload_file.filename, allowed_categories)
        if not valid:
            raise ValidationException(f"Invalid file type: {error}")

        # 获取文件category
        extension = Path(upload_file.filename).suffix.lower()
        file_category = self.get_file_category(extension)

        # 创建safe filename
        safe_filename = self.sanitize_filename(upload_file.filename)

        # 创建subfolder if specified
        if subfolder:
            save_dir = self.upload_dir / subfolder / file_category
        else:
            save_dir = self.upload_dir / file_category

        save_dir.mkdir(parents=True, exist_ok=True)

        # Full保存路径
        file_path = save_dir / safe_filename

        # 保存文件temporarily
        temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

        try:
            # 保存文件
            file_size = 0
            async with aiofiles.open(temp_path, 'wb') as f:
                while chunk := await upload_file.read(8192):  # 8KB chunks
                    file_size += len(chunk)

                    # 检查size during上传
                    max_size = self.MAX_FILE_SIZES.get(file_category, settings.max_upload_size)
                    if file_size > max_size:
                        raise ValidationException(f"File too large. Maximum size is {max_size // (1024*1024)}MB")

                    await f.write(chunk)

            # 校验文件size
            valid, error = self.validate_file_size(file_size, file_category)
            if not valid:
                raise ValidationException(error)

            # 校验MIME type
            valid, error = self.validate_mime_type(temp_path, extension)
            if not valid:
                raise ValidationException(f"File content validation failed: {error}")

            # Calculate文件哈希
            file_hash = self.get_file_hash(temp_path)

            # Move temp文件to final location
            temp_path.rename(file_path)

            # Return文件信息
            return str(file_path.relative_to(self.upload_dir)), {
                "original_filename": upload_file.filename,
                "saved_filename": safe_filename,
                "file_path": str(file_path),
                "relative_path": str(file_path.relative_to(self.upload_dir)),
                "file_size": file_size,
                "file_hash": file_hash,
                "file_category": file_category,
                "mime_type": upload_file.content_type,
                "uploaded_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            # Clean up temp文件on错误
            if temp_path.exists():
                temp_path.unlink()

            if isinstance(e, ValidationException):
                raise

            logger.error(f"File upload error: {e}")
            raise ValidationException(f"Failed to save file: {str(e)}")

    def delete_file(self, file_path: str) -> bool:
        """Safely delete a file"""
        try:
            full_path = self.upload_dir / file_path

            # 校验路径is within上传目录
            if not str(full_path.resolve()).startswith(str(self.upload_dir.resolve())):
                logger.warning(f"Attempted to delete file outside upload directory: {file_path}")
                return False

            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False


# 全局实例
file_validator = FileSecurityValidator()