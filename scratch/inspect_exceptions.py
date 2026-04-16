
try:
    import google.api_core.exceptions as exceptions
    print("Members of google.api_core.exceptions:")
    print([m for m in dir(exceptions) if "AlreadyExists" in m])
except ImportError:
    print("google.api_core.exceptions not found")
