"""
Inspection script for Runner source.
"""
import nest_asyncio
from google.adk import Runner
import inspect

nest_asyncio.apply()

print("Source of Runner.__init__:")
try:
    print(inspect.getsource(Runner.__init__))
except Exception as e:
    print(f"Error getting source: {e}")

print("\nSource of Runner properties:")
# Check if app is a property or attribute
if hasattr(Runner, 'app'):
    attr = getattr(Runner, 'app')
    if isinstance(attr, property):
        print("Found 'app' property.")
        try:
            print(inspect.getsource(attr.fget))
        except:
            print("Could not get source of fget")
    else:
        print(f"'app' is {type(attr)}")
else:
    print("'app' not found in Runner class dict")
