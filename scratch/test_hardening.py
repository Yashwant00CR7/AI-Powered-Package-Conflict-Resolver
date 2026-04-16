
import asyncio
import os
import sys
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lazy_session import LazyDatabaseSessionService
from google.api_core.exceptions import AlreadyExists as AlreadyExistsError
from google.genai import types

async def test_session_hardening():
    print("Testing LazyDatabaseSessionService hardening...")
    
    # Mock the database backend
    # We want super().create_session to raise AlreadyExistsError once
    db_url = "sqlite+aiosqlite:///test_mock.db"
    service = LazyDatabaseSessionService(db_url)
    
    # Mocking super().create_session and super().add_message
    # Since we can't easily mock 'super()' in Python without some tricks, 
    # we'll just test if the imports and try-except blocks are correctly placed by running it.
    
    session_id = "test_collision_id"
    user_id = "user_1"
    app_name = "test_app"
    
    print(f"1. Creating lazy session: {session_id}")
    session = await service.create_session(session_id, user_id, app_name)
    
    print("2. Simulating collision (AlreadyExistsError) on wake up...")
    # To simulate this, we'll monkeypatch the super class method on the instance
    # This is a bit hacky but works for testing the logic in LazyDatabaseSessionService
    
    original_create = service.__class__.__mro__[1].create_session
    
    # Mock that raises AlreadyExistsError
    mock_create = AsyncMock(side_effect=AlreadyExistsError("Session already exists"))
    
    # We need to temporarily replace the base class method for THIS instance
    import unittest.mock
    with unittest.mock.patch('google.adk.sessions.DatabaseSessionService.create_session', mock_create):
        try:
            print("Calling add_message (should trigger wake up with collision)...")
            msg = types.Content(role="user", parts=[types.Part.from_text(text="hello")])
            await service.add_message(session_id, msg)
            print("✅ add_message handled AlreadyExistsError correctly.")
        except Exception as e:
            print(f"❌ add_message failed to handle AlreadyExistsError: {type(e).__name__}: {e}")
            raise

    # Test append_event with collision
    service._pending_sessions[session_id] = {"user_id": user_id, "app_name": app_name, "kwargs": {}}
    
    # For append_event, it also calls get_session on collision
    mock_get = AsyncMock(return_value=MagicMock(last_update_time="now"))
    
    with unittest.mock.patch('google.adk.sessions.DatabaseSessionService.create_session', mock_create):
        with unittest.mock.patch('google.adk.sessions.DatabaseSessionService.get_session', mock_get):
            try:
                print("Calling append_event (should trigger wake up with collision)...")
                await service.append_event(session, {"event": "test"})
                print("✅ append_event handled AlreadyExistsError and synced session correctly.")
            except Exception as e:
                print(f"❌ append_event failed: {type(e).__name__}: {e}")
                raise

if __name__ == "__main__":
    asyncio.run(test_session_hardening())
