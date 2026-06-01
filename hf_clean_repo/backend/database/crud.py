import logging
import re
import json
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select, func
from .models import User, WardrobeItem, Outfit, RefreshToken, OutfitRating, RecommendationFeedback, ItemUsage, ModelMetrics
from typing import Optional, List, Dict, Any
from . import models

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User role types"""
    ADMIN = "admin"
    USER = "user"

class CRUDException(Exception):
    """Base exception for CRUD operations"""
    pass

class UserNotFoundError(CRUDException):
    """Raised when user is not found"""
    pass

class DuplicateEmailError(CRUDException):
    """Raised when email already exists"""
    pass

class DatabaseError(CRUDException):
    """Raised for database operation failures"""
    pass

class ValidationError(CRUDException):
    """Raised for validation failures"""
    pass

class AuthorizationError(CRUDException):
    """Raised when user lacks permission"""
    pass

class PaginationParams:
    """Pagination parameters"""
    def __init__(self, limit: int = 20, offset: int = 0):
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        self.limit = limit
        self.offset = offset

def _validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def _validate_items_json(items_json: str) -> Dict[str, Any]:
    """
    Validate items JSON format and structure.
    
    Expected format: {"items": [{"id": int, "quantity": int}, ...]}
    
    Raises:
        ValidationError: If JSON is invalid or doesn't match schema
    """
    try:
        data = json.loads(items_json)
        
        if not isinstance(data, dict):
            raise ValidationError("JSON must be an object")
        
        if "items" not in data:
            raise ValidationError("JSON must contain 'items' key")
        
        if not isinstance(data["items"], list):
            raise ValidationError("'items' must be an array")
        
        if len(data["items"]) == 0:
            raise ValidationError("'items' array cannot be empty")
        
        for idx, item in enumerate(data["items"]):
            if not isinstance(item, dict):
                raise ValidationError(f"Item {idx} must be an object")
            
            if "id" not in item or not isinstance(item["id"], int) or item["id"] <= 0:
                raise ValidationError(f"Item {idx} must have valid 'id' (positive integer)")
            
            if "quantity" not in item or not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                raise ValidationError(f"Item {idx} must have valid 'quantity' (positive integer)")
        
        return data
    
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON format: {str(e)}")

def _get_requester_role(db: Session, requester_id: int) -> Optional[UserRole]:
    """
    Get requester's role from database.
    
    Returns:
        UserRole if user exists, None otherwise
    """
    try:
        user = db.query(User).filter(User.id == requester_id).first()
        if user and hasattr(user, 'role'):
            role_str = user.role if isinstance(user.role, str) else user.role.value
            return UserRole(role_str)
        return None
    except (SQLAlchemyError, ValueError):
        return None

def _check_user_authorization(db: Session, target_user_id: int, requester_id: int) -> None:
    """
    Check if requester has authorization to access target user's data.
    Admins can access any user's data. Regular users can only access their own.
    
    Raises:
        AuthorizationError: If requester doesn't have permission
    """
    if requester_id is None:
        return
    
    if target_user_id == requester_id:
        return
    
    # Check if requester is admin
    requester_role = _get_requester_role(db, requester_id)
    if requester_role == UserRole.ADMIN:
        logger.info(f"Admin {requester_id} accessing user {target_user_id} data")
        return
    
    logger.warning(f"Unauthorized access attempt: requester {requester_id} (role: {requester_role}) accessing user {target_user_id}")
    raise AuthorizationError("You do not have permission to access this user's data")

def create_user(
    db: Session,
    name: str,
    email: str,
    password_hash: str,
    profile_image_path: Optional[str] = None
) -> User:
    """
    Create a new user with validation and error handling.
    
    Raises:
        ValueError: If email format is invalid or name is empty
        DuplicateEmailError: If email already exists
        DatabaseError: If database operation fails
    """
    try:
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        
        if not email or not _validate_email(email):
            raise ValueError("Invalid email format")

        if not password_hash or not password_hash.strip():
            raise ValueError("Password hash is required")
        
        # Check for existing email
        existing_user = db.query(User).filter(User.email == email.lower()).first()
        if existing_user:
            raise DuplicateEmailError(f"Email '{email}' is already registered")
        
        new_user = User(
            name=name.strip(),
            email=email.lower(),
            password_hash=password_hash.strip(),
            profile_image_path=profile_image_path,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User created successfully: {new_user.id}")
        return new_user
    
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e).lower():
            logger.error(f"Integrity error creating user: email duplicate")
            raise DuplicateEmailError("Email already exists in database")
        logger.error(f"Integrity error creating user: {str(e)}")
        raise DatabaseError(f"Database constraint violation: {str(e)}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating user: {str(e)}")
        raise DatabaseError(f"Database operation failed: {str(e)}")

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve user by email with error handling.
    
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        if not email or not _validate_email(email):
            return None
        
        return db.query(User).filter(User.email == email.lower()).first()
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching user by email: {str(e)}")
        raise DatabaseError(f"Failed to fetch user: {str(e)}")

def get_user_by_email_verification_token(db: Session, token_hash: str) -> Optional[User]:
    """Retrieve a user by email verification token hash."""
    try:
        if not token_hash or not token_hash.strip():
            return None
        return (
            db.query(User)
            .filter(User.email_verification_token_hash == token_hash.strip())
            .first()
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching email verification token: {str(e)}")
        raise DatabaseError(f"Failed to fetch email verification token: {str(e)}")

def set_email_verification_token(
    db: Session,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> Optional[User]:
    """Store the email verification token hash and expiration."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        user.email_verified = False
        user.email_verification_token_hash = token_hash.strip()
        user.email_verification_expires_at = expires_at
        user.email_verified_at = None
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error setting email verification token: {str(e)}")
        raise DatabaseError(f"Failed to set email verification token: {str(e)}")

def mark_email_verified(db: Session, user_id: int) -> Optional[User]:
    """Mark a user as email verified and clear pending verification state."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        user.email_verified = True
        user.email_verified_at = datetime.utcnow()
        user.email_verification_token_hash = None
        user.email_verification_expires_at = None
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error marking email verified: {str(e)}")
        raise DatabaseError(f"Failed to mark email verified: {str(e)}")

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieve user by ID with error handling.
    
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            return None
        
        return db.query(User).filter(User.id == user_id).first()
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching user by ID: {str(e)}")
        raise DatabaseError(f"Failed to fetch user: {str(e)}")

def update_user_password(db: Session, user_id: int, password_hash: str) -> Optional[User]:
    """Update a user's password hash."""
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            return None
        if not password_hash or not password_hash.strip():
            raise ValueError("Password hash is required")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.password_hash = password_hash.strip()
        db.commit()
        db.refresh(user)
        return user

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating user password: {str(e)}")
        raise DatabaseError(f"Failed to update user password: {str(e)}")

def create_refresh_token(
    db: Session,
    user_id: int,
    jti: str,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    replaced_by_jti: Optional[str] = None,
) -> RefreshToken:
    """Persist a refresh token JTI for replay detection and revocation."""
    try:
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            replaced_by_jti=replaced_by_jti,
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating refresh token: {str(e)}")
        raise DatabaseError(f"Failed to create refresh token: {str(e)}")

def get_refresh_token_by_jti(db: Session, jti: str) -> Optional[RefreshToken]:
    """Get a refresh token row by token id (JTI)."""
    try:
        if not jti or not jti.strip():
            return None
        return db.query(RefreshToken).filter(RefreshToken.jti == jti.strip()).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching refresh token: {str(e)}")
        raise DatabaseError(f"Failed to fetch refresh token: {str(e)}")

def revoke_refresh_token(
    db: Session,
    jti: str,
    replaced_by_jti: Optional[str] = None,
    reason: Optional[str] = None,
) -> bool:
    """Revoke one refresh token by JTI."""
    try:
        token = get_refresh_token_by_jti(db, jti)
        if not token:
            return False
        if token.revoked_at is None:
            token.revoked_at = datetime.utcnow()
        if replaced_by_jti:
            token.replaced_by_jti = replaced_by_jti
        if reason:
            token.revoked_reason = reason
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error revoking refresh token: {str(e)}")
        raise DatabaseError(f"Failed to revoke refresh token: {str(e)}")

def revoke_all_user_refresh_tokens(db: Session, user_id: int) -> int:
    """Revoke all active refresh tokens for a user."""
    try:
        now = datetime.utcnow()
        updated = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .update(
                {
                    RefreshToken.revoked_at: now,
                    RefreshToken.revoked_reason: "logout_all_or_reset",
                },
                synchronize_session=False,
            )
        )
        db.commit()
        return int(updated or 0)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error revoking all user refresh tokens: {str(e)}")
        raise DatabaseError(f"Failed to revoke all refresh tokens: {str(e)}")

def list_user_refresh_tokens(db: Session, user_id: int) -> List[RefreshToken]:
    """List refresh token records for a user, newest first."""
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            return []
        return (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.created_at.desc())
            .all()
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error listing user refresh tokens: {str(e)}")
        raise DatabaseError(f"Failed to list refresh tokens: {str(e)}")

def touch_refresh_token_usage(db: Session, jti: str) -> bool:
    """Update last-used timestamp for a refresh token."""
    try:
        token = get_refresh_token_by_jti(db, jti)
        if not token:
            return False
        token.last_used_at = datetime.utcnow()
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating refresh token usage: {str(e)}")
        raise DatabaseError(f"Failed to update refresh token usage: {str(e)}")

def revoke_user_refresh_token(db: Session, user_id: int, jti: str, reason: str = "manual_revoke") -> bool:
    """Revoke a token only if it belongs to the given user."""
    try:
        token = get_refresh_token_by_jti(db, jti)
        if not token or token.user_id != user_id:
            return False
        return revoke_refresh_token(db, jti, reason=reason)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error revoking user refresh token: {str(e)}")
        raise DatabaseError(f"Failed to revoke user refresh token: {str(e)}")

def update_user_analysis(
    db: Session,
    user_id: int,
    height: float,
    weight: float,
    body_shape: str,
    undertone: str,
    bmi: float,
    requester_id: Optional[int] = None
) -> Optional[User]:
    """
    Update user analysis data with role-aware authorization, validation, and transaction handling.
    
    Raises:
        UserNotFoundError: If user doesn't exist
        AuthorizationError: If requester lacks permission
        ValueError: If invalid data provided
        DatabaseError: If database operation fails
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user ID")
        
        _check_user_authorization(db, user_id, requester_id)
        
        if height <= 0 or weight <= 0 or bmi <= 0:
            raise ValueError("Height, weight, and BMI must be positive numbers")
        
        if height > 300:
            raise ValueError("Height value is unrealistic")
        
        if weight > 500:
            raise ValueError("Weight value is unrealistic")
        
        if not body_shape or not body_shape.strip():
            raise ValueError("Body shape cannot be empty")
        
        if not undertone or not undertone.strip():
            raise ValueError("Undertone cannot be empty")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        user.height = height
        user.weight = weight
        user.body_shape = body_shape.strip()
        user.undertone = undertone.strip()
        user.bmi = bmi
        
        db.commit()
        db.refresh(user)
        logger.info(f"User analysis updated: {user_id}")
        return user
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating user analysis: {str(e)}")
        raise DatabaseError(f"Failed to update user analysis: {str(e)}")

def create_wardrobe_item(
    db: Session,
    user_id: int,
    image_path: str,
    clothing_type: str,
    color_primary: str,
    color_secondary: Optional[str] = None,
    pattern: Optional[str] = None,
    season: Optional[str] = None,
    category: Optional[str] = None,
    requester_id: Optional[int] = None
) -> WardrobeItem:
    """
    Create wardrobe item with role-aware authorization, validation, and error handling.
    
    Raises:
        UserNotFoundError: If user doesn't exist
        AuthorizationError: If requester lacks permission
        ValueError: If required fields are invalid
        DatabaseError: If database operation fails
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user ID")
        
        _check_user_authorization(db, user_id, requester_id)
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        if not image_path or not image_path.strip():
            raise ValueError("Image path cannot be empty")
        
        if not clothing_type or not clothing_type.strip():
            raise ValueError("Clothing type cannot be empty")
        
        if not color_primary or not color_primary.strip():
            raise ValueError("Primary color cannot be empty")
        
        new_item = WardrobeItem(
            user_id=user_id,
            image_path=image_path.strip(),
            clothing_type=clothing_type.strip(),
            color_primary=color_primary.strip(),
            color_secondary=color_secondary.strip() if color_secondary else None,
            pattern=pattern.strip() if pattern else None,
            season=season.strip() if season else None,
            category=category.strip() if category else None
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        logger.info(f"Wardrobe item created: {new_item.id} for user {user_id}")
        return new_item
    
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating wardrobe item: {str(e)}")
        raise DatabaseError(f"Failed to create wardrobe item: Database constraint violation")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating wardrobe item: {str(e)}")
        raise DatabaseError(f"Failed to create wardrobe item: {str(e)}")

def get_user_wardrobe(
    db: Session, 
    user_id: int, 
    pagination: Optional[PaginationParams] = None,
    requester_id: Optional[int] = None
) -> List[WardrobeItem]:
    """
    Retrieve paginated wardrobe items for user with role-aware authorization checks.

    Returns:
        List of WardrobeItem objects (pagination applied).
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            return []
        
        _check_user_authorization(db, user_id, requester_id)
        
        if pagination is None:
            pagination = PaginationParams()
        
        # Get paginated items
        items = db.query(WardrobeItem).filter(
            WardrobeItem.user_id == user_id
        ).order_by(WardrobeItem.id.desc()).limit(
            pagination.limit
        ).offset(
            pagination.offset
        ).all()
        
        return items
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching wardrobe: {str(e)}")
        raise DatabaseError(f"Failed to fetch wardrobe items: {str(e)}")

def get_wardrobe_items(
    db: Session, 
    user_id: int, 
    limit: int = 20, 
    offset: int = 0,
    requester_id: Optional[int] = None
) -> List[WardrobeItem]:
    """Alias for get_user_wardrobe returning a list - used by main.py"""
    pagination = PaginationParams(limit=limit, offset=offset)
    return get_user_wardrobe(db, user_id, pagination, requester_id)

def delete_wardrobe_item(
    db: Session, 
    item_id: int, 
    requester_id: Optional[int] = None
) -> bool:
    """
    Delete wardrobe item with role-aware authorization checks and error handling.
    
    Raises:
        AuthorizationError: If requester lacks permission
        DatabaseError: If database operation fails
    """
    try:
        if not isinstance(item_id, int) or item_id <= 0:
            return False
        
        item = db.query(WardrobeItem).filter(WardrobeItem.id == item_id).first()
        if not item:
            logger.warning(f"Wardrobe item {item_id} not found for deletion")
            return False
        
        _check_user_authorization(db, item.user_id, requester_id)
        
        db.delete(item)
        db.commit()
        logger.info(f"Wardrobe item deleted: {item_id}")
        return True
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting wardrobe item: {str(e)}")
        raise DatabaseError(f"Failed to delete wardrobe item: {str(e)}")

def create_outfit(
    db: Session,
    user_id: int,
    name: str,
    items_json: str,
    occasion: Optional[str] = None,
    requester_id: Optional[int] = None
) -> Outfit:
    """
    Create outfit with role-aware authorization, JSON schema validation, and error handling.
    
    Raises:
        UserNotFoundError: If user doesn't exist
        AuthorizationError: If requester lacks permission
        ValidationError: If JSON schema is invalid
        ValueError: If required fields are invalid
        DatabaseError: If database operation fails
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user ID")
        
        _check_user_authorization(db, user_id, requester_id)
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        if not name or not name.strip():
            raise ValueError("Outfit name cannot be empty")
        
        if not items_json or not items_json.strip():
            raise ValueError("Items JSON cannot be empty")
        
        # Validate items JSON schema
        _validate_items_json(items_json)
        
        new_outfit = Outfit(
            user_id=user_id,
            name=name.strip(),
            items_json=items_json.strip(),
            occasion=occasion.strip() if occasion else None
        )
        db.add(new_outfit)
        db.commit()
        db.refresh(new_outfit)
        logger.info(f"Outfit created: {new_outfit.id} for user {user_id}")
        return new_outfit
    
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating outfit: {str(e)}")
        raise DatabaseError(f"Failed to create outfit: Database constraint violation")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating outfit: {str(e)}")
        raise DatabaseError(f"Failed to create outfit: {str(e)}")

def get_user_outfits(
    db: Session, 
    user_id: int, 
    pagination: Optional[PaginationParams] = None,
    requester_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retrieve paginated outfits for user with role-aware authorization checks.
    
    Returns:
        Dict with 'items', 'total', 'limit', 'offset'
    
    Raises:
        AuthorizationError: If requester lacks permission
        DatabaseError: If database operation fails
    """
    try:
        if not isinstance(user_id, int) or user_id <= 0:
            return {"items": [], "total": 0, "limit": 0, "offset": 0}
        
        _check_user_authorization(db, user_id, requester_id)
        
        if pagination is None:
            pagination = PaginationParams()
        
        # Get total count
        total = db.query(func.count(Outfit.id)).filter(
            Outfit.user_id == user_id
        ).scalar()
        
        # Get paginated items
        items = db.query(Outfit).filter(
            Outfit.user_id == user_id
        ).order_by(Outfit.id.desc()).limit(
            pagination.limit
        ).offset(
            pagination.offset
        ).all()
        
        return {
            "items": items,
            "total": total,
            "limit": pagination.limit,
            "offset": pagination.offset
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching outfits: {str(e)}")
        raise DatabaseError(f"Failed to fetch outfits: {str(e)}")


# ============ FEEDBACK & LEARNING FUNCTIONS ============

def create_outfit_rating(
    db: Session,
    user_id: int,
    outfit_id: int,
    rating: int,
    comment: Optional[str] = None,
    requester_id: Optional[int] = None
) -> "models.OutfitRating":
    """
    Create an outfit rating for feedback-driven improvement.
    
    Args:
        db: Database session
        user_id: User rating the outfit
        outfit_id: Outfit being rated
        rating: Rating 1-5
        comment: Optional user comment
        requester_id: User making the request (for authorization)
    
    Returns:
        OutfitRating object
    
    Raises:
        ValidationError: If rating is invalid or outfit not found
        AuthorizationError: If user not authorized
        DatabaseError: If database operation fails
    """
    try:
        if requester_id and requester_id != user_id:
            raise AuthorizationError("Cannot rate outfits for other users")
        
        if not 1 <= rating <= 5:
            raise ValidationError("Rating must be between 1 and 5")
        
        # Verify outfit exists and belongs to user
        outfit = db.query(models.Outfit).filter(
            models.Outfit.id == outfit_id,
            models.Outfit.user_id == user_id
        ).first()
        
        if not outfit:
            raise ValidationError(f"Outfit {outfit_id} not found for user {user_id}")
        
        outfit_rating = models.OutfitRating(
            user_id=user_id,
            outfit_id=outfit_id,
            rating=rating,
            comment=comment[:500] if comment else None
        )
        
        db.add(outfit_rating)
        db.commit()
        db.refresh(outfit_rating)
        
        logger.info(f"Created outfit rating: user={user_id}, outfit={outfit_id}, rating={rating}")
        return outfit_rating
    
    except (ValidationError, AuthorizationError):
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating outfit rating: {str(e)}")
        raise DatabaseError(f"Failed to create outfit rating: {str(e)}")


def create_recommendation_feedback(
    db: Session,
    user_id: int,
    recommendation_type: str,
    recommendation_id: str,
    helpful: bool,
    requester_id: Optional[int] = None
) -> "models.RecommendationFeedback":
    """
    Create feedback on a recommendation (outfit, shopping, discard).
    
    Args:
        db: Database session
        user_id: User providing feedback
        recommendation_type: "outfit" | "shopping" | "discard"
        recommendation_id: ID of the recommendation
        helpful: True if helpful, False otherwise
        requester_id: User making the request (for authorization)
    
    Returns:
        RecommendationFeedback object
    
    Raises:
        ValidationError: If inputs invalid
        AuthorizationError: If user not authorized
        DatabaseError: If database operation fails
    """
    try:
        if requester_id and requester_id != user_id:
            raise AuthorizationError("Cannot provide feedback for other users")
        
        if recommendation_type not in ["outfit", "shopping", "discard"]:
            raise ValidationError(f"Invalid recommendation_type: {recommendation_type}")
        
        feedback = models.RecommendationFeedback(
            user_id=user_id,
            recommendation_type=recommendation_type,
            recommendation_id=str(recommendation_id),
            helpful=1 if helpful else 0
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"Created recommendation feedback: user={user_id}, type={recommendation_type}, helpful={helpful}")
        return feedback
    
    except (ValidationError, AuthorizationError):
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating recommendation feedback: {str(e)}")
        raise DatabaseError(f"Failed to create recommendation feedback: {str(e)}")


def create_item_usage(
    db: Session,
    user_id: int,
    item_id: int,
    action: str,
    wear_count: int = 1,
    requester_id: Optional[int] = None
) -> "models.ItemUsage":
    """
    Track wardrobe item usage (worn, kept, discarded).
    
    Args:
        db: Database session
        user_id: Item owner
        item_id: Wardrobe item ID
        action: "kept" | "discarded" | "worn"
        wear_count: Number of times worn (default 1)
        requester_id: User making the request (for authorization)
    
    Returns:
        ItemUsage object
    
    Raises:
        ValidationError: If inputs invalid or item not found
        AuthorizationError: If user not authorized
        DatabaseError: If database operation fails
    """
    try:
        if requester_id and requester_id != user_id:
            raise AuthorizationError("Cannot track usage for other users' items")
        
        if action not in ["kept", "discarded", "worn"]:
            raise ValidationError(f"Invalid action: {action}")
        
        if wear_count < 0:
            raise ValidationError("wear_count must be non-negative")
        
        # Verify item exists and belongs to user
        item = db.query(models.WardrobeItem).filter(
            models.WardrobeItem.id == item_id,
            models.WardrobeItem.user_id == user_id
        ).first()
        
        if not item:
            raise ValidationError(f"Wardrobe item {item_id} not found for user {user_id}")
        
        usage = models.ItemUsage(
            user_id=user_id,
            item_id=item_id,
            action=action,
            wear_count=max(1, wear_count)
        )
        
        db.add(usage)
        db.commit()
        db.refresh(usage)
        
        logger.info(f"Created item usage: user={user_id}, item={item_id}, action={action}")
        return usage
    
    except (ValidationError, AuthorizationError):
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating item usage: {str(e)}")
        raise DatabaseError(f"Failed to create item usage: {str(e)}")


def create_model_metric(
    db: Session,
    model_name: str,
    metric_type: str,
    value: float,
    version: Optional[str] = None
) -> "models.ModelMetrics":
    """
    Store model performance metric for monitoring and retraining decisions.
    
    Args:
        db: Database session
        model_name: "color_harmony" | "clothing_classifier" | "body_shape"
        metric_type: "accuracy" | "avg_rating" | "helpful_rate" | "drift_score"
        value: Metric value
        version: Optional model version/epoch identifier
    
    Returns:
        ModelMetrics object
    
    Raises:
        ValidationError: If inputs invalid
        DatabaseError: If database operation fails
    """
    try:
        if model_name not in ["color_harmony", "clothing_classifier", "body_shape"]:
            raise ValidationError(f"Invalid model_name: {model_name}")
        
        if metric_type not in ["accuracy", "avg_rating", "helpful_rate", "drift_score"]:
            raise ValidationError(f"Invalid metric_type: {metric_type}")
        
        if not 0 <= value <= 1:
            raise ValidationError("Metric value must be between 0 and 1")
        
        metric = models.ModelMetrics(
            model_name=model_name,
            metric_type=metric_type,
            value=value,
            version=version
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        logger.info(f"Created model metric: model={model_name}, type={metric_type}, value={value}")
        return metric
    
    except ValidationError:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating model metric: {str(e)}")
        raise DatabaseError(f"Failed to create model metric: {str(e)}")


def get_feedback_for_period(
    db: Session,
    days: int = 30,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fetch all feedback collected in the last N days for retraining.
    
    Args:
        db: Database session
        days: Lookback period in days (default 30)
        limit: Max results per category
    
    Returns:
        Dict with outfit_ratings, rec_feedback, item_usage counts
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        ratings = db.query(models.OutfitRating).filter(
            models.OutfitRating.created_at >= cutoff_date
        ).limit(limit).all()
        
        rec_feedback = db.query(models.RecommendationFeedback).filter(
            models.RecommendationFeedback.created_at >= cutoff_date
        ).limit(limit).all()
        
        usage = db.query(models.ItemUsage).filter(
            models.ItemUsage.created_at >= cutoff_date
        ).limit(limit).all()
        
        return {
            "outfit_ratings": ratings,
            "recommendation_feedback": rec_feedback,
            "item_usage": usage,
            "total_feedback": len(ratings) + len(rec_feedback) + len(usage),
            "cutoff_date": cutoff_date
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching feedback: {str(e)}")
        raise DatabaseError(f"Failed to fetch feedback: {str(e)}")


def get_model_metrics(
    db: Session,
    model_name: str,
    limit: int = 10
) -> List[models.ModelMetrics]:
    """
    Fetch recent model metrics for a specific model.
    
    Args:
        db: Database session
        model_name: Model to fetch metrics for
        limit: Max results
    
    Returns:
        List of ModelMetrics ordered by most recent first
    """
    try:
        return db.query(models.ModelMetrics).filter(
            models.ModelMetrics.model_name == model_name
        ).order_by(
            models.ModelMetrics.evaluation_date.desc()
        ).limit(limit).all()
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching model metrics: {str(e)}")
        raise DatabaseError(f"Failed to fetch model metrics: {str(e)}")