from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from ..database import get_db
from ..security import security_manager, get_current_user_session
from ..db_session_store import session_store
from .. import schemas, models, crud

logger = logging.getLogger(__name__)

# Create a specific dependency for endpoints that have path parameters
async def get_current_user_for_session_ops(user_session_cookie: str = Cookie(None, alias="session_id"), db: Session = Depends(get_db)):
    """Get current user from secure server-side session for session operations."""
    if not user_session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found. Please login.",
        )
    
    session_data = session_store.get_session(user_session_cookie, db=db)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please login again.",
        )
    
    return {
        "email": session_data["user_email"],
        "session_id": user_session_cookie,
        "session_data": session_data
    }

# Create router
router = APIRouter(
    prefix="/secure-auth",
    tags=["secure-authentication"],
    responses={401: {"model": schemas.ErrorResponse}},
)

@router.post(
    "/login",
    response_model=dict,
    summary="Secure session-based login",
    description="Authenticate user and create secure server-side session."
)
async def secure_login(
    user_credentials: schemas.UserLogin, 
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and create secure server-side session."""
    try:
        # Find user by email
        user = crud.crud.get_user_by_email(db, email=user_credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not security_manager.verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Create secure server-side session in database
        session_id = security_manager.create_session(user.email, db=db)
        
        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            max_age=1800,  # 30 minutes
            httponly=True,  # Cannot be accessed by JavaScript
            secure=False,   # Set to True in production with HTTPS
            samesite="lax"  # CSRF protection
        )
        
        logger.info(f"Secure session created for user: {user.email}")
        
        return {
            "message": "Login successful",
            "user": {
                "email": user.email,
                "name": user.name
            },
            "session_expires_in": 1800  # 30 minutes in seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during secure login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post(
    "/logout",
    summary="Secure logout",
    description="Logout user and destroy server-side session."
)
async def secure_logout(
    response: Response,
    current_user_data: dict = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Logout user and destroy server-side session from database."""
    try:
        session_id = current_user_data.get("session_id")
        
        # Delete session from database
        security_manager.delete_session(session_id, db=db)
        
        # Clear the cookie
        response.delete_cookie(key="session_id")
        
        logger.info(f"User logged out: {current_user_data['email']}")
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.get(
    "/me",
    response_model=schemas.UserCreateResponse,
    summary="Get current user (secure)",
    description="Get information about the currently authenticated user using secure sessions."
)
async def get_current_user_info_secure(
    current_user_data: dict = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Get current user information using secure session."""
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
    "/extend-session",
    summary="Extend session",
    description="Extend the current session expiration time."
)
async def extend_session(
    current_user_data: dict = Depends(get_current_user_session)
):
    """Extend the current session expiration time."""
    try:
        session_id = current_user_data.get("session_id")
        
        if security_manager.extend_session(session_id):
            return {
                "message": "Session extended successfully",
                "new_expires_in": 1800  # 30 more minutes
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extend session"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/sessions",
    summary="Get user sessions",
    description="Get all active sessions for the current user."
)
async def get_user_sessions(
    current_user_data: dict = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Get all active sessions for the current user from database."""
    try:
        sessions = session_store.get_user_sessions(current_user_data["email"], db=db)
        
        return {
            "active_sessions": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete(
    "/sessions/{session_id}",
    summary="Terminate specific session",
    description="Terminate a specific session by ID."
)
async def terminate_session(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_for_session_ops),
    db: Session = Depends(get_db)
):
    """Terminate a specific session by ID."""
    try:
        # Verify the session belongs to the current user
        user_sessions = session_store.get_user_sessions(current_user_data["email"], db=db)
        target_session = None
        for session in user_sessions:
            if session["session_id"] == session_id:
                target_session = session
                break
        
        if not target_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or doesn't belong to you"
            )
        
        # Don't allow terminating current session via this endpoint
        if session_id == current_user_data["session_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot terminate current session. Use logout instead."
            )
        
        # Terminate the session
        success = security_manager.delete_session(session_id, db=db)
        
        if success:
            logger.info(f"Session {session_id} terminated by user {current_user_data['email']}")
            return {"message": "Session terminated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to terminate session"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error terminating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/logout-all",
    summary="Logout from all devices",
    description="Terminate all sessions for the current user."
)
async def logout_all_devices(
    response: Response,
    current_user_data: dict = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Logout user from all devices by terminating all sessions."""
    try:
        user_email = current_user_data["email"]
        
        # Delete all sessions for the user
        terminated_count = security_manager.delete_all_user_sessions(user_email, db=db)
        
        # Clear the cookie
        response.delete_cookie(key="session_id")
        
        logger.info(f"User {user_email} logged out from all devices ({terminated_count} sessions terminated)")
        
        return {
            "message": f"Successfully logged out from all devices",
            "terminated_sessions": terminated_count
        }
        
    except Exception as e:
        logger.error(f"Error during logout from all devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )

@router.post(
    "/extend-session",
    summary="Extend current session",
    description="Extend the expiration time of the current session."
)
async def extend_current_session(
    extend_data: dict,
    current_user_data: dict = Depends(get_current_user_session),
    db: Session = Depends(get_db)
):
    """Extend the current session expiration time."""
    try:
        session_id = current_user_data["session_id"]
        minutes = extend_data.get("minutes", 30)
        
        # Validate minutes (between 5 and 480 minutes = 8 hours max)
        if not isinstance(minutes, int) or minutes < 5 or minutes > 480:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minutes must be between 5 and 480"
            )
        
        # Extend the session
        success = security_manager.extend_session(session_id, minutes, db=db)
        
        if success:
            logger.info(f"Session {session_id} extended by {minutes} minutes for user {current_user_data['email']}")
            return {
                "message": f"Session extended by {minutes} minutes",
                "extended_minutes": minutes
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extend session. Session may be expired or invalid."
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )