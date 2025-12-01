import google.adk
import inspect

print("google.adk contents:")
print(dir(google.adk))

try:
    from google.adk import types
    print("\ngoogle.adk.types contents:")
    print(dir(types))
except ImportError:
    print("\ngoogle.adk.types not found")

try:
    import google.adk.events
    print("\ngoogle.adk.events contents:")
    print(dir(google.adk.events))
except ImportError:
    print("\ngoogle.adk.events not found")

# Search for ModelResponse recursively (shallow)
print("\nSearching for ModelResponse...")
def search_module(module, name, depth=0):
    if depth > 2: return
    for attr in dir(module):
        if attr == name:
            print(f"FOUND: {module.__name__}.{attr}")
        
        # Recurse into submodules if possible
        # (Skipping for safety/speed, just checking top level and known submodules)

if hasattr(google.adk, 'ModelResponse'):
    print("Found google.adk.ModelResponse")

try:
    from google.adk import model_response
    print("Found google.adk.model_response module")
except ImportError:
    print("google.adk.model_response module NOT found")
