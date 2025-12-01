
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

try:
    print("Testing imports...")
    from google.adk.agents.invocation_context import InvocationContext
    print("✅ InvocationContext imported successfully")
except ImportError as e:
    print(f"❌ InvocationContext import failed: {e}")
except Exception as e:
    print(f"❌ InvocationContext error: {e}")

try:
    from google.adk.agents.run_config import RunConfig
    print("✅ RunConfig imported successfully")
except ImportError as e:
    print(f"❌ RunConfig import failed: {e}")
except Exception as e:
    print(f"❌ RunConfig error: {e}")

try:
    from src.agents import create_root_agent
    print("✅ src.agents imported successfully")
except Exception as e:
    print(f"❌ src.agents import failed: {e}")
