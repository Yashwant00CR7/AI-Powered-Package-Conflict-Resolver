
from typing import Optional, Dict, Any, List, AsyncGenerator
from google.adk.sessions import DatabaseSessionService, Session
from google.genai import types
import uuid
from .utils import logger

class LazyDatabaseSessionService(DatabaseSessionService):
    """
    A session service that defers database insertion until the first message is added.
    This prevents empty sessions from cluttering the database on page loads.
    """
    def __init__(self, db_url: str):
        super().__init__(db_url=db_url)
        # In-memory store for pending sessions: {session_id: {metadata}}
        self._pending_sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(self, session_id: str, user_id: str, app_name: str, **kwargs) -> Session:
        """
        Overrides create_session to store metadata in memory instead of DB.
        """
        logger.info(f"💤 Lazy Session Created (Pending): {session_id}")
        
        # Store metadata for later
        self._pending_sessions[session_id] = {
            "user_id": user_id,
            "app_name": app_name,
            "kwargs": kwargs
        }
        
        # Return a temporary Session object (not persisted yet)
        # FIX: Session model expects 'id', not 'session_id'. And no 'history'.
        return Session(
            id=session_id,
            user_id=user_id,
            app_name=app_name
        )

    async def get_session(self, session_id: str, **kwargs) -> Optional[Session]:
        """
        Checks pending sessions first, then falls back to DB.
        FIX: Added **kwargs to match base signature (which accepts app_name etc.)
        """
        # 1. Check pending
        if session_id in self._pending_sessions:
            meta = self._pending_sessions[session_id]
            # Return a fresh Session object from memory metadata
            return Session(
                id=session_id,
                user_id=meta["user_id"],
                app_name=meta["app_name"]
            )
            
        # 2. Check DB (Super)
        # FIX: DatabaseSessionService.get_session likely only accepts session_id
        return await super().get_session(session_id)

    async def add_message(self, session_id: str, message: types.Content) -> None:
        """
        On first message, persists the session to DB before adding the message.
        """
        # 1. Check if this is a pending session
        if session_id in self._pending_sessions:
            logger.info(f"⏰ Waking up Lazy Session: {session_id}")
            meta = self._pending_sessions.pop(session_id)
            
            # Persist the session now!
            # We call super().create_session to actually write to DB
            await super().create_session(
                session_id=session_id,
                user_id=meta["user_id"],
                app_name=meta["app_name"],
                **meta["kwargs"]
            )
            logger.info(f"💾 Session {session_id} persisted to DB.")
            
        # 2. Add the message (Super)
        await super().add_message(session_id, message)

    async def list_sessions(self, app_name: str = None, **kwargs) -> List[Session]:
        """
        Overrides list_sessions to EXCLUDE pending sessions.
        FIX: Updated signature to match base class (likely just app_name or kwargs).
        The error said "takes 1 positional argument but 5 were given", which implies
        it might be defined as `list_sessions(self, app_name: str = None)` or similar.
        Safe bet is to accept kwargs and pass them through.
        """
        # Only return sessions that are actually in the DB
        return await super().list_sessions(app_name, **kwargs)
