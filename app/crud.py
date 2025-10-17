from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from . import models, schemas
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class UserCRUD:
    """CRUD operations for User model with error handling and logging."""
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[models.User]:
        """Get a user by ID.
        
        Args:
            db: Database session
            user_id: User ID to retrieve
            
        Returns:
            User object if found, None otherwise
        """
        try:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                logger.info(f"Retrieved user with ID: {user_id}")
            else:
                logger.warning(f"User not found with ID: {user_id}")
            return user
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            raise
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get a user by email.
        
        Args:
            db: Database session
            email: Email to search for
            
        Returns:
            User object if found, None otherwise
        """
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            if user:
                logger.info(f"Retrieved user with email: {email}")
            return user
        except Exception as e:
            logger.error(f"Error retrieving user by email {email}: {e}")
            raise
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
        """Get all users with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of User objects
        """
        try:
            users = db.query(models.User).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(users)} users (skip={skip}, limit={limit})")
            return users
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            raise
    
    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate) -> models.User:
        """Create a new user.
        
        Args:
            db: Database session
            user: User data to create
            
        Returns:
            Created User object
            
        Raises:
            IntegrityError: If email already exists
        """
        try:
            db_user = models.User(**user.model_dump())
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"Created user with ID: {db_user.id}, email: {db_user.email}")
            return db_user
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error creating user: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
        """Update a user.
        
        Args:
            db: Database session
            user_id: ID of user to update
            user_update: Updated user data
            
        Returns:
            Updated User object if found, None otherwise
            
        Raises:
            IntegrityError: If email already exists for another user
        """
        try:
            db_user = db.query(models.User).filter(models.User.id == user_id).first()
            if not db_user:
                logger.warning(f"User not found for update with ID: {user_id}")
                return None
            
            # Update only provided fields
            update_data = user_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)
            
            db.commit()
            db.refresh(db_user)
            logger.info(f"Updated user with ID: {user_id}")
            return db_user
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating user {user_id}: {e}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user.
        
        Args:
            db: Database session
            user_id: ID of user to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            db_user = db.query(models.User).filter(models.User.id == user_id).first()
            if not db_user:
                logger.warning(f"User not found for deletion with ID: {user_id}")
                return False
            
            db.delete(db_user)
            db.commit()
            logger.info(f"Deleted user with ID: {user_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise

# Create CRUD instance
crud = UserCRUD()