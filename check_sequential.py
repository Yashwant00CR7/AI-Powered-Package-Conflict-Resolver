
from google.adk.agents import SequentialAgent
import inspect

print("=== SequentialAgent Source (run method) ===")
try:
    print(inspect.getsource(SequentialAgent.run))
except Exception as e:
    print(f"Could not get source: {e}")
    print(dir(SequentialAgent))
