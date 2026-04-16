
try:
    from google.api_core.exceptions import AlreadyExists
    print(f"Found AlreadyExists in google.api_core.exceptions")
except ImportError:
    print("Could not find google.api_core.exceptions")

try:
    from google.api_core.exceptions import AlreadyExists as AlreadyExistsError
    print("Can import AlreadyExists as AlreadyExistsError")
except ImportError:
    pass

try:
    # Check if google-adk has it
    from google.adk.sessions import DatabaseSessionService
    # Try to see where create_session might raise from
    print("Imported DatabaseSessionService")
except Exception as e:
    print(f"Error: {e}")
