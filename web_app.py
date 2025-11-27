"""
Web Interface Entry Point for ADK Web UI.
Run with: adk web web_app.py --no-reload
"""
import nest_asyncio
from google.adk import Runner
from src.config import get_session_service
from src.agents import create_root_agent
from src.utils import logger

# Apply nest_asyncio to handle event loop conflicts in the web server
nest_asyncio.apply()

logger.info("🌐 Initializing Web Interface...")

# Initialize Session Service
# We use the same SQLite database as the CLI
session_service = get_session_service()

# Initialize the Root Agent
# This is the agent that will process the web queries
agent = create_root_agent()

# Initialize Runner
# The ADK Web UI looks for a 'runner' or 'agent' instance
runner = Runner(
    agent=agent,
    app_name="package_conflict_resolver_web",
    session_service=session_service
)

logger.info("✅ Web Interface Ready. Run 'adk web web_app.py --no-reload' to start.")
