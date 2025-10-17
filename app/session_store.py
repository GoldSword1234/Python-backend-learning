"""
Server-side session storage for secure token management.
"""
import uuid
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SessionStore:
    """In-memory session store for secure token management."""
    
    def __init__(self):
        # In production, use Redis, database, or other persistent storage
        self._sessions: Dict[str, Dict] = {}
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
    
    def create_session(self, user_email: str, expires_in_minutes: int = 30) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
        
        self._sessions[session_id] = {
            "user_email": user_email,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "last_accessed": datetime.now()
        }
        
        logger.info(f"Created session {session_id} for user {user_email}")
        self._cleanup_expired_sessions()
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by session ID."""
        if not session_id or session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        # Check if session is expired
        if datetime.now() > session["expires_at"]:
            self.delete_session(session_id)
            return None
        
        # Update last accessed time
        session["last_accessed"] = datetime.now()
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            user_email = self._sessions[session_id].get("user_email", "unknown")
            del self._sessions[session_id]
            logger.info(f"Deleted session {session_id} for user {user_email}")
            return True
        return False
    
    def delete_user_sessions(self, user_email: str) -> int:
        """Delete all sessions for a specific user."""
        sessions_to_delete = [
            sid for sid, session in self._sessions.items()
            if session.get("user_email") == user_email
        ]
        
        for session_id in sessions_to_delete:
            del self._sessions[session_id]
        
        logger.info(f"Deleted {len(sessions_to_delete)} sessions for user {user_email}")
        return len(sessions_to_delete)
    
    def extend_session(self, session_id: str, additional_minutes: int = 30) -> bool:
        """Extend session expiration time."""
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        session["expires_at"] = datetime.now() + timedelta(minutes=additional_minutes)
        session["last_accessed"] = datetime.now()
        
        return True
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        
        # Only run cleanup every 5 minutes
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        now = datetime.now()
        expired_sessions = [
            sid for sid, session in self._sessions.items()
            if now > session["expires_at"]
        ]
        
        for session_id in expired_sessions:
            user_email = self._sessions[session_id].get("user_email", "unknown")
            del self._sessions[session_id]
            logger.debug(f"Cleaned up expired session {session_id} for user {user_email}")
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        self._last_cleanup = current_time
    
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        self._cleanup_expired_sessions()
        return len(self._sessions)
    
    def get_user_sessions(self, user_email: str) -> list:
        """Get all active sessions for a user."""
        return [
            {
                "session_id": sid,
                "created_at": session["created_at"],
                "last_accessed": session["last_accessed"],
                "expires_at": session["expires_at"]
            }
            for sid, session in self._sessions.items()
            if session.get("user_email") == user_email and datetime.now() <= session["expires_at"]
        ]

# Global session store instance
session_store = SessionStore()