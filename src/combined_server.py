"""
Combined Server for AI-Package-Doctor.
Runs both the ADK Web UI and the MCP Server on the same FastAPI app.
"""
import os
import uvicorn
import nest_asyncio
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request

# ADK Imports
from google.adk.cli.adk_web_server import (
    AdkWebServer, BaseAgentLoader, EvalSetsManager, EvalSetResultsManager,
    BaseCredentialService
)
from google.adk.artifacts import FileArtifactService
from src.config import get_session_service, get_memory_service
from src.agents import create_root_agent
from src.utils import logger
from typing import Optional, Any

# Apply nest_asyncio
nest_asyncio.apply()

# --- 1. ADK Setup Classes ---

class SingleAgentLoader(BaseAgentLoader):
    """Custom loader that serves our single root agent."""
    def __init__(self, agent):
        self.agent = agent
        self.agent_name = "package_conflict_resolver"

    def list_agents(self) -> list[str]:
        return [self.agent_name]

    def load_agent(self, agent_name: str):
        if agent_name == self.agent_name:
            return self.agent
        raise ValueError(f"Agent {agent_name} not found")

class LocalCredentialService(BaseCredentialService):
    """Simple credential service implementation."""
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def load_credential(self, auth_config: Any, callback_context: Any) -> Optional[Any]:
        return None

    def save_credential(self, auth_config: Any, callback_context: Any) -> None:
        pass

# --- 2. Initialize Services & Agent ---

logger.info("🌐 Initializing Services...")
session_service = get_session_service()
memory_service = get_memory_service()

data_dir = os.path.abspath("data")
os.makedirs(data_dir, exist_ok=True)

artifact_service = FileArtifactService(root_dir=os.path.join(data_dir, "artifacts"))
credential_service = LocalCredentialService(base_dir=os.path.join(data_dir, "credentials"))
# Import concrete implementations
from google.adk.evaluation.local_eval_sets_manager import LocalEvalSetsManager
from google.adk.evaluation.local_eval_set_results_manager import LocalEvalSetResultsManager

eval_sets_manager = LocalEvalSetsManager(base_dir=os.path.join(data_dir, "eval_sets"))
eval_set_results_manager = LocalEvalSetResultsManager(base_dir=os.path.join(data_dir, "eval_results"))

logger.info("🤖 Creating Root Agent...")
root_agent = create_root_agent()
agent_loader = SingleAgentLoader(root_agent)

# --- 3. Create ADK Web App ---

logger.info("🚀 Creating ADK Web Server...")
adk_server = AdkWebServer(
    agent_loader=agent_loader,
    session_service=session_service,
    memory_service=memory_service,
    artifact_service=artifact_service,
    credential_service=credential_service,
    eval_sets_manager=eval_sets_manager,
    eval_set_results_manager=eval_set_results_manager,
    agents_dir=os.path.abspath("src")
)

# This is the main FastAPI app
app = adk_server.get_fast_api_app()

# --- 4. Create MCP Server ---

logger.info("🔌 Creating MCP Server...")
mcp = FastMCP("AI-Package-Doctor")

@mcp.tool()
async def solve_dependency_issue(issue_description: str) -> str:
    """
    Analyzes and resolves Python dependency conflicts based on a description.
    
    Args:
        issue_description: A detailed description of the dependency problem, error logs, or requirements.txt content.
    """
    from google.adk import Runner
    from google.genai import types
    import uuid

    session_id = f"mcp-session-{uuid.uuid4()}"
    logger.info(f"MCP Tool Called: solve_dependency_issue (Session: {session_id})")

    # Create session
    await session_service.create_session(
        session_id=session_id,
        user_id="mcp_user",
        app_name="package_conflict_resolver"
    )

    runner = Runner(
        agent=root_agent,
        app_name="package_conflict_resolver",
        session_service=session_service
    )

    user_msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=issue_description)]
    )

    response_text = ""
    
    # Run agent and collect response
    # Note: This runs synchronously in the async function, blocking this request.
    # Ideally we'd stream, but for a simple tool return we collect all.
    response_generator = runner.run(
        session_id=session_id,
        user_id="mcp_user",
        new_message=user_msg
    )

    for event in response_generator:
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            if event.content.parts:
                text = event.content.parts[0].text
                if text and text != "None":
                    response_text += text
        elif hasattr(event, 'text'):
            response_text += event.text
        elif isinstance(event, str):
            response_text += event

    return response_text

# --- 5. Mount MCP to FastAPI ---

# FastMCP provides a way to mount itself, but we want to be explicit about the SSE endpoint
# to ensure it works with the existing app.
# We will use the mcp.mount_to_fastapi method if available, or manually add the routes.

# FastMCP's mount_to_fastapi is the easiest way
mcp.mount_to_fastapi(app, path="/mcp")

logger.info("✅ Combined Server Configured")
logger.info("👉 Web UI: http://0.0.0.0:7860/dev-ui/")
logger.info("👉 MCP SSE: http://0.0.0.0:7860/mcp/sse")

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
