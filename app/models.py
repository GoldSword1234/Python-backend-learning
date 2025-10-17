from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
from .database import Base

class User(Base):
    """User model for storing user information.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        name: User's full name (required)
        email: User's email address (required, unique)
        age: User's age (optional)
        bio: User's biography (optional)
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


class Session(Base):
    """Session model for storing user sessions in database.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        session_id: Unique session identifier (UUID)
        user_email: Email of the authenticated user
        created_at: When the session was created
        expires_at: When the session expires
        last_accessed: When the session was last accessed
        is_active: Whether the session is still active
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Session(id={self.id}, session_id='{self.session_id}', user_email='{self.user_email}')>"
    
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def extend_session(self, minutes: int = 30):
        """Extend the session expiration time."""
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self.last_accessed = datetime.now(timezone.utc)