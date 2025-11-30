
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
        # FIX: Handle None session_id (generate one if missing)
        if not session_id:
            session_id = str(uuid.uuid4())
            
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
        # FIX: Pass session_id, app_name, and user_id as keyword arguments
        return await super().get_session(
            session_id=session_id,
            app_name=kwargs.get("app_name"),
            user_id=kwargs.get("user_id")
        )

    async def add_message(self, session_id: str, message: types.Content) -> None:
        """
        On first message, persists the session to DB before adding the message.
        Note: The Runner might call append_event directly, so we handle it there too.
        """
        # 1. Check if this is a pending session
        if session_id in self._pending_sessions:
            logger.info(f"⏰ Waking up Lazy Session (add_message): {session_id}")
            meta = self._pending_sessions.pop(session_id)
            
            # Persist the session now!
            await super().create_session(
                session_id=session_id,
                user_id=meta["user_id"],
                app_name=meta["app_name"],
                **meta["kwargs"]
            )
            logger.info(f"💾 Session {session_id} persisted to DB.")
            
        # 2. Add the message (Super)
        await super().add_message(session_id=session_id, message=message)

    async def append_event(self, session: Session, event: Any) -> None:
        """
        Overrides append_event to ensure session exists in DB before appending.
        The Runner calls this method to add user messages/events.
        """
        session_id = session.id
        
        # 1. Check if this is a pending session
        if session_id in self._pending_sessions:
            logger.info(f"⏰ Waking up Lazy Session (append_event): {session_id}")
            meta = self._pending_sessions.pop(session_id)
            
            # Persist the session now!
            persisted_session = await super().create_session(
                session_id=session_id,
                user_id=meta["user_id"],
                app_name=meta["app_name"],
                **meta["kwargs"]
            )
            logger.info(f"💾 Session {session_id} persisted to DB.")
            
            # FIX: Update the passed session object with the fresh timestamp from the DB
            # This prevents "stale session" errors in append_event
            if hasattr(persisted_session, 'last_update_time'):
                session.last_update_time = persisted_session.last_update_time
            
        # 2. Append the event (Super)
        await super().append_event(session=session, event=event)

    async def list_sessions(self, app_name: str = None, **kwargs) -> List[Session]:
        """
        Overrides list_sessions to EXCLUDE pending sessions.
        FIX: Updated signature to match base class (likely just app_name or kwargs).
        The error said "takes 1 positional argument but 5 were given", which implies
        it might be defined as `list_sessions(self, app_name: str = None)` or similar.
        Safe bet is to accept kwargs and pass them through.
        """
        # Only return sessions that are actually in the DB
        # FIX: Pass app_name as keyword argument to avoid "takes 1 positional argument" error
        return await super().list_sessions(app_name=app_name, **kwargs)
