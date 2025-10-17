"""
Database-backed session storage for secure token management.
"""
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_

from .models import Session
from .database import get_db

logger = logging.getLogger(__name__)

class DatabaseSessionStore:
    """Database-backed session store for secure token management."""
    
    def __init__(self):
        self._default_expires_minutes = 30
    
    def create_session(self, user_email: str, expires_in_minutes: int = None, db: DBSession = None) -> str:
        """Create a new session in the database and return session ID."""
        if expires_in_minutes is None:
            expires_in_minutes = self._default_expires_minutes
            
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        
        # Create database session
        db_session = Session(
            session_id=session_id,
            user_email=user_email,
            expires_at=expires_at,
            is_active=True
        )
        
        if db is None:
            # If no db session provided, create one
            from .database import SessionLocal
            db = SessionLocal()
            try:
                db.add(db_session)
                db.commit()
                db.refresh(db_session)
            finally:
                db.close()
        else:
            # Use provided db session
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
        
        logger.info(f"Created database session {session_id} for user {user_email}")
        
        # Clean up expired sessions periodically
        self._cleanup_expired_sessions(db if db else None)
        
        return session_id
    
    def get_session(self, session_id: str, db: DBSession = None) -> Optional[Dict]:
        """Get session data by session ID from database."""
        if not session_id:
            return None
        
        # Get database session
        if db is None:
            from .database import SessionLocal
            db = SessionLocal()
            try:
                db_session = db.query(Session).filter(
                    and_(
                        Session.session_id == session_id,
                        Session.is_active == True
                    )
                ).first()
            finally:
                db.close()
        else:
            db_session = db.query(Session).filter(
                and_(
                    Session.session_id == session_id,
                    Session.is_active == True
                )
            ).first()
        
        if not db_session:
            return None
        
        # Check if session is expired
        if db_session.is_expired():
            self.delete_session(session_id, db)
            return None
        
        # Update last accessed time
        db_session.last_accessed = datetime.now(timezone.utc)
        if db is None:
            from .database import SessionLocal
            temp_db = SessionLocal()
            try:
                temp_db.merge(db_session)
                temp_db.commit()
            finally:
                temp_db.close()
        else:
            db.commit()
        
        # Return session data as dict
        return {
            "user_email": db_session.user_email,
            "created_at": db_session.created_at,
            "expires_at": db_session.expires_at,
            "last_accessed": db_session.last_accessed,
            "session_id": db_session.session_id
        }
    
    def delete_session(self, session_id: str, db: DBSession = None) -> bool:
        """Delete session from database by session ID."""
        if not session_id:
            return False
        
        if db is None:
            from .database import SessionLocal
            db = SessionLocal()
            try:
                db_session = db.query(Session).filter(Session.session_id == session_id).first()
                if db_session:
                    db_session.is_active = False
                    db.commit()
                    logger.info(f"Deactivated database session {session_id}")
                    return True
            finally:
                db.close()
        else:
            db_session = db.query(Session).filter(Session.session_id == session_id).first()
            if db_session:
                db_session.is_active = False
                db.commit()
                logger.info(f"Deactivated database session {session_id}")
                return True
        
        return False
    
    def extend_session(self, session_id: str, minutes: int = 30, db: DBSession = None) -> bool:
        """Extend session expiration time."""
        if not session_id:
            return False
        
        if db is None:
            from .database import SessionLocal
            db = SessionLocal()
            try:
                db_session = db.query(Session).filter(
                    and_(
                        Session.session_id == session_id,
                        Session.is_active == True
                    )
                ).first()
                if db_session and not db_session.is_expired():
                    db_session.extend_session(minutes)
                    db.commit()
                    logger.info(f"Extended database session {session_id} by {minutes} minutes")
                    return True
            finally:
                db.close()
        else:
            db_session = db.query(Session).filter(
                and_(
                    Session.session_id == session_id,
                    Session.is_active == True
                )
            ).first()
            if db_session and not db_session.is_expired():
                db_session.extend_session(minutes)
                db.commit()
                logger.info(f"Extended database session {session_id} by {minutes} minutes")
                return True
        
        return False
    
    def get_user_sessions(self, user_email: str, db: DBSession = None) -> list:
        """Get all active sessions for a user."""
        if db is None:
            from .database import SessionLocal
            db = SessionLocal()
            try:
                sessions = db.query(Session).filter(
                    and_(
                        Session.user_email == user_email,
                        Session.is_active == True
                    )
                ).all()
                return [
                    {
                        "session_id": s.session_id,
                        "created_at": s.created_at,
                        "expires_at": s.expires_at,
                        "last_accessed": s.last_accessed
                    }
                    for s in sessions if not s.is_expired()
                ]
            finally:
                db.close()
        else:
            sessions = db.query(Session).filter(
                and_(
                    Session.user_email == user_email,
                    Session.is_active == True
                )
            ).all()
            return [
                {
                    "session_id": s.session_id,
                    "created_at": s.created_at,
                    "expires_at": s.expires_at,
                    "last_accessed": s.last_accessed
                }
                for s in sessions if not s.is_expired()
            ]
    
    def delete_all_user_sessions(self, user_email: str, db: DBSession = None) -> int:
        """Delete all sessions for a user (logout from all devices)."""
        if db is None:
            from .database import SessionLocal
            db = SessionLocal()
            try:
                sessions = db.query(Session).filter(
                    and_(
                        Session.user_email == user_email,
                        Session.is_active == True
                    )
                ).all()
                count = len(sessions)
                for session in sessions:
                    session.is_active = False
                db.commit()
                logger.info(f"Deactivated {count} sessions for user {user_email}")
                return count
            finally:
                db.close()
        else:
            sessions = db.query(Session).filter(
                and_(
                    Session.user_email == user_email,
                    Session.is_active == True
                )
            ).all()
            count = len(sessions)
            for session in sessions:
                session.is_active = False
            db.commit()
            logger.info(f"Deactivated {count} sessions for user {user_email}")
            return count
    
    def _cleanup_expired_sessions(self, db: DBSession = None):
        """Clean up expired sessions from database."""
        try:
            if db is None:
                from .database import SessionLocal
                db = SessionLocal()
                try:
                    # Deactivate expired sessions
                    expired_sessions = db.query(Session).filter(
                        and_(
                            Session.expires_at < datetime.now(timezone.utc),
                            Session.is_active == True
                        )
                    ).all()
                    
                    count = len(expired_sessions)
                    if count > 0:
                        for session in expired_sessions:
                            session.is_active = False
                        db.commit()
                        logger.info(f"Cleaned up {count} expired sessions")
                finally:
                    db.close()
            else:
                # Deactivate expired sessions
                expired_sessions = db.query(Session).filter(
                    and_(
                        Session.expires_at < datetime.now(timezone.utc),
                        Session.is_active == True
                    )
                ).all()
                
                count = len(expired_sessions)
                if count > 0:
                    for session in expired_sessions:
                        session.is_active = False
                    db.commit()
                    logger.info(f"Cleaned up {count} expired sessions")
                    
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

# Global session store instance
session_store = DatabaseSessionStore()