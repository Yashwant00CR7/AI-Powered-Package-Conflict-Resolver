import json
from google.adk.events import Event

try:
    print("Event Schema:")
    print(json.dumps(Event.model_json_schema(), indent=2))
except Exception as e:
    print(f"Error inspecting Event: {e}")
    # Fallback: print dir
    print(dir(Event))
