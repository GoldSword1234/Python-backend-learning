from datetime import datetime, timedelta
from typing import Optional, Union
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .db_session_store import session_store
from .database import get_db

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing with Argon2 (no length limits, most secure)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Token scheme
security = HTTPBearer()

class SecurityManager:
    """Handles authentication and authorization."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password using Argon2."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_session(user_email: str, db: Session = None) -> str:
        """Create a secure server-side session in database."""
        return session_store.create_session(user_email, expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES, db=db)
    
    @staticmethod
    def get_session_data(session_id: str, db: Session = None) -> Optional[dict]:
        """Get session data from database."""
        return session_store.get_session(session_id, db=db)
    
    @staticmethod
    def delete_session(session_id: str, db: Session = None) -> bool:
        """Delete session from database."""
        return session_store.delete_session(session_id, db=db)
    
    @staticmethod
    def extend_session(session_id: str, minutes: int = 30, db: Session = None) -> bool:
        """Extend session expiration time."""
        return session_store.extend_session(session_id, minutes, db=db)
    
    @staticmethod
    def get_user_sessions(user_email: str, db: Session = None) -> list:
        """Get all active sessions for a user."""
        return session_store.get_user_sessions(user_email, db=db)
    
    @staticmethod
    def delete_all_user_sessions(user_email: str, db: Session = None) -> int:
        """Delete all sessions for a user (logout from all devices)."""
        return session_store.delete_all_user_sessions(user_email, db=db)
        """Delete a session from server-side store."""
        return session_store.delete_session(session_id)
    
    @staticmethod
    def extend_session(session_id: str) -> bool:
        """Extend session expiration."""
        return session_store.extend_session(session_id)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_email: str = payload.get("sub")
            if user_email is None:
                return None
            return {"email": user_email, "exp": payload.get("exp")}
        except JWTError:
            return None

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = SecurityManager.verify_token(token)
        if payload is None:
            raise credentials_exception
        
        user_email = payload.get("email")
        if user_email is None:
            raise credentials_exception
            
        # Here you would typically fetch the user from database
        # For now, we'll return the email
        return {"email": user_email}
        
    except Exception:
        raise credentials_exception

# Dependency to get current user from secure server-side session
async def get_current_user_session(
    session_cookie: str = Cookie(None, alias="session_id"), 
    session_header: str = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db)
):
    """Get current user from secure server-side session stored in database.
    
    Supports both cookie-based authentication (for web browsers) and 
    header-based authentication (for API testing in Swagger UI).
    """
    # Try to get session ID from either cookie or header
    session_id = session_cookie or session_header
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session found. Please login.",
        )
    
    session_data = session_store.get_session(session_id, db=db)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please login again.",
        )
    
    return {
        "email": session_data["user_email"],
        "session_id": session_id,
        "session_data": session_data
    }

# Optional: Dependency for admin users
async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Ensure current user is an admin."""
    # You can add admin check logic here
    # For example, check if user has admin role in database
    return current_user

# Create instance
security_manager = SecurityManager()