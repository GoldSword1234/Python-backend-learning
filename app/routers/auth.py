from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..database import get_db
from ..security import security_manager, get_current_user
from .. import schemas, models, crud

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"model": schemas.ErrorResponse}},
)

@router.post(
    "/register",
    response_model=schemas.UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password."
)
async def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = crud.crud.get_user_by_email(db, email=user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        password_hash = security_manager.get_password_hash(user_data.password)
        
        # Create user in database
        db_user = models.User(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash,
            age=user_data.age,
            bio=user_data.bio
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"New user registered: {user_data.email}")
        return db_user
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="User login",
    description="Authenticate user and return JWT token."
)
async def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    try:
        # Find user by email
        user = crud.crud.get_user_by_email(db, email=user_credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not security_manager.verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = security_manager.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes in seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.get(
    "/me",
    response_model=schemas.UserCreateResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user."
)
async def get_current_user_info(
    current_user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information."""
    try:
        user = crud.crud.get_user_by_email(db, email=current_user_data["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/change-password",
    summary="Change password",
    description="Change the password for the currently authenticated user."
)
async def change_password(
    old_password: str,
    new_password: str,
    current_user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    try:
        user = crud.crud.get_user_by_email(db, email=current_user_data["email"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify old password
        if not security_manager.verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        # Update password
        user.password_hash = security_manager.get_password_hash(new_password)
        db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )