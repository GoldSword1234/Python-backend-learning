from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import logging

from ..database import get_db
from ..security import get_current_user
from ..crud import crud
from .. import schemas, models

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"model": schemas.ErrorResponse}},
)

@router.get(
    "/",
    response_model=schemas.UserSummaryList,
    summary="Get all users",
    description="Retrieve a list of all users with basic info (id, name, email) and optional pagination. Requires authentication."
)
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    order_by: str = Query("id", description="Field to order by: id, name, email, created_at"),
    order_direction: str = Query("asc", description="Order direction: asc or desc"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all users with pagination and ordering."""
    try:
        # Build query with ordering
        query = db.query(models.User)
        
        # Add ordering
        if order_by and hasattr(models.User, order_by):
            order_field = getattr(models.User, order_by)
            if order_direction.lower() == "desc":
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())
        else:
            query = query.order_by(models.User.id.asc())
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        total = db.query(models.User).count()
        
        return schemas.UserSummaryList(users=users, total=total)
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving users"
        )

@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID. Requires authentication."
)
async def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a user by ID."""
    try:
        user = crud.get_user(db, user_id=user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving user"
        )

@router.post(
    "/",
    response_model=schemas.UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided information. Requires authentication."
)
async def create_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user."""
    try:
        # Check if user with email already exists
        existing_user = crud.get_user_by_email(db, email=user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        return crud.create_user(db=db, user=user)
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating user"
        )

@router.put(
    "/{user_id}",
    response_model=schemas.User,
    summary="Update user by ID",
    description="Update a user's information by their ID. Requires authentication."
)
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a user by ID."""
    try:
        # Check if user exists
        existing_user = crud.get_user(db, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        
        # Check if email is being updated and already exists for another user
        if user_update.email:
            email_user = crud.get_user_by_email(db, email=user_update.email)
            if email_user and email_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        updated_user = crud.update_user(db=db, user_id=user_id, user_update=user_update)
        return updated_user
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating user"
        )
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user by ID",
    description="Delete a user by their ID. Requires authentication."
)
async def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user by ID."""
    try:
        # Check if user exists
        existing_user = crud.get_user(db, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        crud.delete_user(db=db, user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while deleting user"
        )