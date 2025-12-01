try:
    from google.adk.types import ModelResponse
    print("SUCCESS: Found ModelResponse in google.adk.types")
except ImportError:
    print("FAILURE: ModelResponse NOT found in google.adk.types")

try:
    from google.adk import ModelResponse
    print("SUCCESS: Found ModelResponse in google.adk")
except ImportError:
    print("FAILURE: ModelResponse NOT found in google.adk")
