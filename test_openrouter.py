import os
import asyncio
import sys
from dotenv import load_dotenv

# Add current directory to path so we can import src
sys.path.append(os.getcwd())

async def test_model():
    print("Loading configuration...")
    load_dotenv()
    
    try:
        from src.config import get_model
        model = get_model()
        
        print(f"Model initialized: {model._primary_models[0]}")
        print("Sending test prompt to OpenRouter...")
        
        prompt = "Hello! Are you working? Please respond with a short confirmation like 'Yes, I am working!'"
        
        print("\n--- Response Start ---")
        full_response = ""
        async for chunk in model.generate_content_async(prompt):
            # LiteLLM/ADK chunks might be strings or objects depending on version
            # We'll try to extract the text content
            text_chunk = str(chunk)
            if hasattr(chunk, 'text'):
                text_chunk = chunk.text
            
            print(text_chunk, end="", flush=True)
            full_response += text_chunk
        print("\n--- Response End ---\n")
        
        if full_response.strip():
            print("SUCCESS: OpenRouter Model Test")
        else:
            print("WARNING: OpenRouter Model Test - EMPTY RESPONSE")
            
    except Exception as e:
        print(f"\nFAILURE: OpenRouter Model Test")
        print(f"Error details: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_model())
