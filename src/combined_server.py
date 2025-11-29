"""
Combined Server for AI-Package-Doctor.
Runs both the ADK Web UI and the MCP Server on the same FastAPI app.
"""
import os
import uvicorn
import nest_asyncio
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

# ADK Imports
from google.adk.cli.adk_web_server import (
    AdkWebServer, BaseAgentLoader, EvalSetsManager, EvalSetResultsManager,
    BaseCredentialService
)
from google.adk.artifacts import FileArtifactService
# Import concrete implementations
from google.adk.evaluation.local_eval_sets_manager import LocalEvalSetsManager
from google.adk.evaluation.local_eval_set_results_manager import LocalEvalSetResultsManager

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

# Use concrete managers with correct arguments
eval_sets_manager = LocalEvalSetsManager(agents_dir=data_dir)
eval_set_results_manager = LocalEvalSetResultsManager(agents_dir=data_dir)

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

# --- 4. Create MCP Server (Standard Implementation) ---

logger.info("🔌 Creating MCP Server...")
mcp_server = Server("AI-Package-Doctor")

@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="solve_dependency_issue",
            description="Analyzes and resolves Python dependency conflicts based on a description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_description": {
                        "type": "string",
                        "description": "A detailed description of the dependency problem, error logs, or requirements.txt content."
                    }
                },
                "required": ["issue_description"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "solve_dependency_issue":
        issue_description = arguments.get("issue_description")
        if not issue_description:
            raise ValueError("Missing issue_description")

        from google.adk import Runner
        from google.genai import types as genai_types
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

        user_msg = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=issue_description)]
        )

        response_text = ""
        
        # Run agent and collect response
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

        return [types.TextContent(type="text", text=response_text)]
    
    raise ValueError(f"Unknown tool: {name}")

# --- 5. Mount MCP SSE Endpoint ---

# We need to manage the SSE transport manually
sse_transport = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def handle_sse(request: Request):
    async with mcp_server.run_sse(sse_transport) as streams:
        async def event_generator():
            async for message in streams[1]:
                yield message
        
        return EventSourceResponse(event_generator())

@app.post("/mcp/messages")
async def handle_messages(request: Request):
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    return {}

logger.info("✅ Combined Server Configured")
logger.info("👉 Web UI: http://0.0.0.0:7860/dev-ui/")
logger.info("👉 MCP SSE: http://0.0.0.0:7860/mcp/sse")

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
