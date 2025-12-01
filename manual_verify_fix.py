import sys
import os

with open('src/agents.py', 'r') as f:
    content = f.read()
    if 'async def run_async(self, input_str: str, **kwargs):' in content:
        print("SUCCESS: run_async is defined in src/agents.py")
    else:
        print("FAILURE: run_async is NOT defined in src/agents.py")
