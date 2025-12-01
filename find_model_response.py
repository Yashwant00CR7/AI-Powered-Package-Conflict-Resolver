import google.adk
import os
import sys

# Get package path
package_path = os.path.dirname(google.adk.__file__)
print(f"ADK Package Path: {package_path}")

# Walk through the package and search for ModelResponse
print("Searching for 'class ModelResponse' in package files...")

found = False
for root, dirs, files in os.walk(package_path):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "class ModelResponse" in content:
                        print(f"\nFOUND in: {path}")
                        # Calculate relative import path
                        rel_path = os.path.relpath(path, os.path.dirname(package_path))
                        module_path = rel_path.replace(os.sep, ".").replace(".py", "")
                        # Remove __init__ if present
                        if module_path.endswith(".__init__"):
                            module_path = module_path[:-9]
                        print(f"Import suggestion: from {module_path} import ModelResponse")
                        found = True
            except Exception as e:
                print(f"Could not read {path}: {e}")

if not found:
    print("\nModelResponse class NOT found in the package files.")
    # Print top level files to give a clue
    print("\nTop level files in google.adk:")
    print(os.listdir(package_path))
