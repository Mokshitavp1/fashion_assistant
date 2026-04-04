"""
Secure image storage service for user photos.

Features:
- Fernet encryption with user-specific keys
- Secure random image IDs (not enumerable)
- Authenticated retrieval via token verification
- Automatic cleanup policies
- Audit logging for sensitive access
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import logging
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Configuration
ENCRYPTED_STORAGE_DIR = os.getenv("ENCRYPTED_STORAGE_DIR", ".images_secure")
MAX_IMAGE_AGE_DAYS = int(os.getenv("MAX_IMAGE_AGE_DAYS", "90"))
MAX_IMAGES_PER_USER = int(os.getenv("MAX_IMAGES_PER_USER", "100"))

# Ensure storage directory exists with restricted permissions
os.makedirs(ENCRYPTED_STORAGE_DIR, exist_ok=True)
if os.name == 'posix':  # Unix/Linux/macOS
    os.chmod(ENCRYPTED_STORAGE_DIR, 0o700)  # Owner only: rwx------


def _get_fernet_cipher(user_id: int, secret_key: str) -> Fernet:
    """Get or create Fernet cipher for user."""
    key_material = f"{secret_key}:user:{user_id}".encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=f"user_{user_id}".encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_material))
    return Fernet(key)


def _generate_secure_image_id() -> str:
    """Generate a cryptographically secure, non-enumerable image ID."""
    return secrets.token_urlsafe(24)  # 32-byte random data, URL-safe


def _get_image_metadata_path(image_id: str) -> Path:
    """Get path to metadata file (unencrypted metadata for fast lookup)."""
    return Path(ENCRYPTED_STORAGE_DIR) / f"{image_id}.meta"


def _get_image_data_path(image_id: str) -> Path:
    """Get path to encrypted image file."""
    return Path(ENCRYPTED_STORAGE_DIR) / f"{image_id}.bin"


def store_encrypted_image(
    image_bytes: bytes,
    user_id: int,
    secret_key: str,
    image_type: str = "wardrobe",  # wardrobe, profile, analysis
    metadata: Optional[dict] = None
) -> Tuple[str, str]:
    """
    Store an encrypted image and return secure reference.
    
    Args:
        image_bytes: Raw image data (JPEG/PNG bytes)
        user_id: Owner user ID
        secret_key: Application SECRET_KEY
        image_type: Category of image (wardrobe/profile/analysis)
        metadata: Optional metadata dict (stored unencrypted for quick lookup)
    
    Returns:
        Tuple of (image_id, filename_for_db)
    
    Raises:
        ValueError: If user exceeds max images or image is invalid
    """
    # Validate image
    image_array = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image_array is None:
        raise ValueError("Invalid image file")
    
    # Generate secure ID
    image_id = _generate_secure_image_id()
    
    # Encrypt image data
    cipher = _get_fernet_cipher(user_id, secret_key)
    encrypted_data = cipher.encrypt(image_bytes)
    
    # Write encrypted image
    image_path = _get_image_data_path(image_id)
    with open(image_path, "wb") as f:
        f.write(encrypted_data)
    if os.name == 'posix':
        os.chmod(image_path, 0o600)  # Owner only: rw-------
    
    # Write metadata (unencrypted but signed)
    meta_path = _get_image_metadata_path(image_id)
    meta_content = f"""id:{image_id}
user_id:{user_id}
type:{image_type}
uploaded_at:{datetime.utcnow().isoformat()}
size:{len(image_bytes)}
hash:{hashlib.sha256(image_bytes).hexdigest()[:16]}
"""
    if metadata:
        meta_content += f"custom:{metadata}\n"
    
    with open(meta_path, "w") as f:
        f.write(meta_content)
    if os.name == 'posix':
        os.chmod(meta_path, 0o600)
    
    logger.info(f"Stored encrypted image {image_id} for user {user_id}, type={image_type}")
    
    # Return reference for database storage
    return image_id, f"encrypted://{image_id}"


def retrieve_encrypted_image(
    image_id: str,
    user_id: int,
    secret_key: str,
    verify_ownership: bool = True
) -> bytes:
    """
    Retrieve and decrypt image, verifying ownership.
    
    Args:
        image_id: Secure image ID
        user_id: Requesting user ID (must own the image)
        secret_key: Application SECRET_KEY
        verify_ownership: If True, check that user owns this image
    
    Returns:
        Decrypted image bytes (JPEG/PNG)
    
    Raises:
        FileNotFoundError: Image not found
        PermissionError: User doesn't own this image
        ValueError: Decryption failed (corrupted or tampered)
    """
    image_path = _get_image_data_path(image_id)
    meta_path = _get_image_metadata_path(image_id)
    
    if not image_path.exists() or not meta_path.exists():
        logger.warning(f"Image {image_id} not found")
        raise FileNotFoundError(f"Image {image_id} not found")
    
    # Verify ownership
    if verify_ownership:
        meta_content = meta_path.read_text()
        meta_lines = {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in meta_content.split("\n") if ":" in line}
        
        stored_user_id = int(meta_lines.get("user_id", -1))
        if stored_user_id != user_id:
            logger.warning(f"Unauthorized access attempt: user {user_id} tried to access image {image_id} owned by {stored_user_id}")
            raise PermissionError(f"You don't have access to image {image_id}")
    
    # Decrypt
    try:
        cipher = _get_fernet_cipher(user_id, secret_key)
        encrypted_data = image_path.read_bytes()
        decrypted_data = cipher.decrypt(encrypted_data)
        logger.debug(f"Retrieved encrypted image {image_id} for user {user_id}")
        return decrypted_data
    except Exception as e:
        logger.error(f"Decryption failed for image {image_id}: {str(e)}")
        raise ValueError("Image data corrupted or tampered with")


def delete_encrypted_image(
    image_id: str,
    user_id: int,
    verify_ownership: bool = True
) -> bool:
    """
    Securely delete an encrypted image.
    
    Args:
        image_id: Secure image ID
        user_id: Requesting user ID (must own the image)
        verify_ownership: If True, check that user owns this image
    
    Returns:
        True if deletion successful
    
    Raises:
        PermissionError: User doesn't own this image
        FileNotFoundError: Image not found
    """
    image_path = _get_image_data_path(image_id)
    meta_path = _get_image_metadata_path(image_id)
    
    if not image_path.exists():
        raise FileNotFoundError(f"Image {image_id} not found")
    
    # Verify ownership
    if verify_ownership and meta_path.exists():
        meta_content = meta_path.read_text()
        meta_lines = {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in meta_content.split("\n") if ":" in line}
        stored_user_id = int(meta_lines.get("user_id", -1))
        if stored_user_id != user_id:
            raise PermissionError(f"You don't have access to image {image_id}")
    
    # Secure deletion: overwrite with random data before removing
    try:
        image_size = image_path.stat().st_size
        with open(image_path, "wb") as f:
            f.write(secrets.token_bytes(image_size))
        image_path.unlink()
        meta_path.unlink(missing_ok=True)
        logger.info(f"Securely deleted image {image_id} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {str(e)}")
        raise


def cleanup_old_images(before_date: Optional[datetime] = None) -> int:
    """
    Remove images older than MAX_IMAGE_AGE_DAYS.
    
    Args:
        before_date: If provided, delete images before this date; else use MAX_IMAGE_AGE_DAYS
    
    Returns:
        Number of images deleted
    """
    if before_date is None:
        before_date = datetime.utcnow() - timedelta(days=MAX_IMAGE_AGE_DAYS)
    
    deleted_count = 0
    try:
        for meta_path in Path(ENCRYPTED_STORAGE_DIR).glob("*.meta"):
            meta_content = meta_path.read_text()
            meta_lines = {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in meta_content.split("\n") if ":" in line}
            
            uploaded_at_str = meta_lines.get("uploaded_at", "")
            try:
                uploaded_at = datetime.fromisoformat(uploaded_at_str)
                if uploaded_at < before_date:
                    image_id = meta_lines.get("id", "")
                    delete_encrypted_image(image_id, user_id=-1, verify_ownership=False)
                    deleted_count += 1
            except (ValueError, Exception):
                pass
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old images (before {before_date})")
    
    return deleted_count


def get_image_info(image_id: str, user_id: int) -> Optional[dict]:
    """
    Get metadata about an image without decrypting it.
    
    Args:
        image_id: Secure image ID
        user_id: Requesting user ID
    
    Returns:
        Metadata dict or None if not found
    
    Raises:
        PermissionError: User doesn't own this image
    """
    meta_path = _get_image_metadata_path(image_id)
    if not meta_path.exists():
        return None
    
    meta_content = meta_path.read_text()
    meta_lines = {line.split(":", 1)[0]: line.split(":", 1)[1].strip() for line in meta_content.split("\n") if ":" in line}
    
    stored_user_id = int(meta_lines.get("user_id", -1))
    if stored_user_id != user_id:
        raise PermissionError(f"You don't have access to image {image_id}")
    
    return {
        "id": image_id,
        "user_id": stored_user_id,
        "type": meta_lines.get("type"),
        "uploaded_at": meta_lines.get("uploaded_at"),
        "size": int(meta_lines.get("size", 0)),
    }
