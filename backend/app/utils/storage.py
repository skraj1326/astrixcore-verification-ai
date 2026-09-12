"""Storage utilities for file operations."""

import os
import uuid
from pathlib import Path
from typing import BinaryIO
from app.core.config import settings


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Remove path components
    name = os.path.basename(filename)
    # Remove dangerous characters
    name = "".join(c for c in name if c.isalnum() or c in "._-")
    # Limit length
    if len(name) > 255:
        name = name[:255]
    return name


def generate_unique_filename(original: str) -> str:
    """Generate a unique filename preserving extension."""
    sanitized = sanitize_filename(original)
    name, ext = os.path.splitext(sanitized)
    unique_id = uuid.uuid4().hex[:8]
    return f"{name}_{unique_id}{ext}"


def save_uploaded_file(file_data: bytes, subdir: str, filename: str) -> str:
    """Save uploaded file to storage."""
    storage_path = settings.STORAGE_ROOT / subdir
    storage_path.mkdir(parents=True, exist_ok=True)

    unique_name = generate_unique_filename(filename)
    file_path = storage_path / unique_name

    with open(file_path, "wb") as f:
        f.write(file_data)

    return str(file_path)


def read_file(file_path: str) -> str:
    """Read text file safely."""
    path = Path(file_path)
    # Ensure path is within storage
    try:
        path.resolve().relative_to(settings.STORAGE_ROOT.resolve())
    except ValueError:
        raise PermissionError("File access denied")

    with open(path, "r") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    """Write text file safely."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(content)


def delete_file(file_path: str) -> bool:
    """Delete file safely."""
    path = Path(file_path)
    try:
        path.resolve().relative_to(settings.STORAGE_ROOT.resolve())
    except ValueError:
        raise PermissionError("File access denied")

    if path.exists():
        path.unlink()
        return True
    return False


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    path = Path(file_path)
    return path.stat().st_size if path.exists() else 0


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file_size(file_data: bytes) -> bool:
    """Validate file size is within limits."""
    return len(file_data) <= MAX_FILE_SIZE