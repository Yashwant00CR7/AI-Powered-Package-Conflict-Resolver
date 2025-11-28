"""
Main entry point for the AI-Powered Package Conflict Resolver.
Initializes and runs the agent with a test query.
"""
import asyncio
import os
import nest_asyncio
from google.adk import Runner
from google.genai import types
from src.config import get_session_service
from src.agents import create_root_agent
from src.utils import logger

# Apply nest_asyncio to handle event loop conflicts
nest_asyncio.apply()


async def run_session(runner, user_input: str, session_id: str):
    """
    Runs an agent session with the given input.
    
    Args:
        runner: The Runner instance
        user_input: User's query/request
        session_id: Session identifier for state tracking
    """
    logger.info(f"🚀 Starting session: {session_id}")
    logger.info(f"📝 User input: {user_input}")
    
    # Create structured message
    user_msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_input)]
    )
    
    # Run the agent
    response_generator = runner.run(
        session_id=session_id,
        user_id="default_user",
        new_message=user_msg
    )
    
    # Collect and display response
    full_response = ""
    print("\n🤖 Agent Response:\n")
    for event in response_generator:
        # ADK events have .content.parts structure
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            if event.content.parts:
                text = event.content.parts[0].text
                # Filter out empty or "None" responses
                if text and text != "None":
                    print(text, end='', flush=True)
                    full_response += text
        # Fallback for simple text
        elif hasattr(event, 'text'):
            text = event.text
            print(text, end='', flush=True)
            full_response += text
        elif isinstance(event, str):
            print(event, end='', flush=True)
            full_response += event
    
    print("\n")
    logger.info(f"✅ Session completed: {session_id}")
    return full_response


async def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("🤖 AI-Powered Package Conflict Resolver - Starting...")
    logger.info("=" * 60)
    
    # Initialize session service
    session_service = get_session_service()
    
    # Create root agent
    root_agent = create_root_agent()
    
    # Initialize runner
    runner = Runner(
        agent=root_agent,
        app_name="package_conflict_resolver",
        session_service=session_service
    )
    logger.info("✅ Runner initialized")
    
    # Test query
    test_query = """
    I have a legacy Python project with the following dependencies in requirements.txt:
    
    pydantic==1.10.2
    fastapi==0.95.0
    
    I'm getting deprecation warnings about regex patterns in Pydantic. 
    Can you help me fix this and update to compatible versions?
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Running test query...")
    logger.info("=" * 60 + "\n")
    
    # Explicitly create the session first to avoid "Session not found" error
    # Delete existing DB to ensure clean state
    if os.path.exists("package_conflict_resolver.db"):
        try:
            os.remove("package_conflict_resolver.db")
            logger.info("🗑️  Removed existing database file")
        except Exception as e:
            logger.warning(f"⚠️  Could not remove DB: {e}")

    session_id = "test_session_001"
    try:
        # Pass app_name to ensure Runner finds it
        await session_service.create_session(
            session_id=session_id, 
            user_id="default_user",
            app_name="package_conflict_resolver"
        )
        logger.info(f"✅ Created new session: {session_id}")
    except Exception as e:
        logger.warning(f"⚠️  Session creation note: {e}")

    # Run the session
    response = await run_session(
        runner=runner,
        user_input=test_query,
        session_id=session_id
    )
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Test completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
