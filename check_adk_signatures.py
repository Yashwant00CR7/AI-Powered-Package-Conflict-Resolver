
from google.adk.sessions import DatabaseSessionService, Session
import inspect
from pydantic import BaseModel

print("=== Session Class Fields ===")
try:
    if issubclass(Session, BaseModel):
        print(Session.model_fields.keys())
    else:
        print(Session.__annotations__)
except Exception as e:
    print(f"Error inspecting Session: {e}")
    # Fallback
    print(dir(Session))

print("\n=== DatabaseSessionService.get_session Signature ===")
print(inspect.signature(DatabaseSessionService.get_session))

print("\n=== DatabaseSessionService.list_sessions Signature ===")
print(inspect.signature(DatabaseSessionService.list_sessions))
