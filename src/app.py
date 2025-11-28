"""
App definition for the AI-Powered Package Conflict Resolver.
Includes Events Compaction configuration.
"""
from google.adk import App
from google.adk.types import EventsCompactionConfig
from .agents import root_agent
from .utils import logger
from .config import get_memory_service, get_session_service

# Define the App with Events Compaction and Custom Services
package_conflict_resolver_app = App(
    name="Package_Conflict_Resolver_App",
    root_agent=root_agent,
    memory_service=get_memory_service(),
    session_service=get_session_service(),
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,  # Trigger compaction every 3 invocations
        overlap_size=1,         # Keep 1 previous turn for context
    ),
)

logger.info("✅ Package Conflict Resolver App created with Events Compaction (Interval: 3, Overlap: 1)")
