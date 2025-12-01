import asyncio
import sys
import os
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from agents import create_web_crawl_agent

async def main():
    print("--- Creating WebCrawlAgent ---")
    try:
        agent = create_web_crawl_agent()
        print(f"Agent created: {agent}")
        print(f"Agent type: {type(agent)}")
    except Exception as e:
        print(f"Failed to create agent: {e}")
        return

    input_text = "Please check https://example.com for me."
    print(f"--- Running Agent with input: '{input_text}' ---")
    
    try:
        # Call run_async directly (it returns an async generator)
        # We need to mock InvocationContext
        from google.adk.agents.invocation_context import InvocationContext
        ctx = InvocationContext(input_data=input_text)
        
        print("--- Iterating over events ---")
        async for event in agent.run_async(ctx):
            print(f"Event: {event}")
            if event.action == 'model_response':
                print(f"Result Text: {event.payload.text}")
    except Exception as e:
        print(f"Error running agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
