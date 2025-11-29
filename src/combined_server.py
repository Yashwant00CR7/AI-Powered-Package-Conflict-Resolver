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

# Calculate web_assets_dir dynamically
import google.adk.cli
web_assets_dir = os.path.join(os.path.dirname(google.adk.cli.__file__), "browser")
logger.info(f"📂 Serving Web UI from: {web_assets_dir}")

# This is the main FastAPI app
app = adk_server.get_fast_api_app(web_assets_dir=web_assets_dir)

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
    logger.info(f"🔧 Tool called: {name} with arguments: {arguments}")
    
    try:
        if name == "solve_dependency_issue":
            issue_description = arguments.get("issue_description") if arguments else None
            if not issue_description:
                error_msg = "Missing issue_description parameter"
                logger.error(f"❌ {error_msg}")
                return [types.TextContent(type="text", text=f"Error: {error_msg}")]

            from google.adk import Runner
            from google.genai import types as genai_types
            import uuid

            session_id = f"mcp-session-{uuid.uuid4()}"
            logger.info(f"✅ Processing tool call (Session: {session_id})")
            logger.info(f"📝 Issue description: {issue_description[:100]}...")

            try:
                # Create session
                await session_service.create_session(
                    session_id=session_id,
                    user_id="mcp_user",
                    app_name="package_conflict_resolver"
                )
                logger.info(f"✅ Session created: {session_id}")

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
                logger.info("🤖 Running agent...")
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

                logger.info(f"✅ Agent completed. Response length: {len(response_text)} chars")
                
                if not response_text:
                    response_text = "No response generated from agent. Please check server logs."
                
                return [types.TextContent(type="text", text=response_text)]
            
            except Exception as e:
                error_msg = f"Error running agent: {str(e)}"
                logger.error(f"❌ {error_msg}", exc_info=True)
                return [types.TextContent(type="text", text=f"Error: {error_msg}")]
        
        error_msg = f"Unknown tool: {name}"
        logger.error(f"❌ {error_msg}")
        return [types.TextContent(type="text", text=f"Error: {error_msg}")]
    
    except Exception as e:
        error_msg = f"Unexpected error in tool handler: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {error_msg}")]

# --- 5. Mount MCP SSE Endpoint ---

# We need to manage the SSE transport manually using raw ASGI routes
sse_transport = SseServerTransport("/mcp/messages")

async def handle_sse(request: Request):
    """
    Handler for SSE endpoint.
    Returns an ASGI app that manages the connection.
    """
    async def sse_asgi_app(scope, receive, send):
        async with sse_transport.connect_sse(scope, receive, send) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options()
            )
    return sse_asgi_app

async def handle_messages(request: Request):
    """
    Handler for Messages endpoint.
    Returns the ASGI app from sse_transport.
    """
    return sse_transport.handle_post_message

# Add routes directly to the FastAPI app (which is a Starlette app)
app.add_route("/mcp/sse", handle_sse, methods=["GET"])
app.add_route("/mcp/messages", handle_messages, methods=["POST"])

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/dev-ui/")

# --- Add Builder Route (Fixes 404) ---
from fastapi.responses import PlainTextResponse, FileResponse
from pathlib import Path

@app.get(
    "/builder/app/{app_name}",
    response_model_exclude_none=True,
    response_class=PlainTextResponse,
)
async def get_agent_builder(
    app_name: str,
    file_path: Optional[str] = None,
    tmp: Optional[bool] = False,
):
    # We use the same agents_dir as defined above
    agents_path = Path(os.path.abspath("src"))
    agent_dir = agents_path # In our case, src is the root for the agent code
    
    # If app_name is "package_conflict_resolver", it might be looking for a subdir
    # But our code is in src/agents.py. 
    # The standard ADK structure has agents_dir/app_name/root_agent.yaml
    # We don't have that structure or YAML files.
    # So we just return empty string to satisfy the UI, as we are code-first.
    
    return ""

logger.info("✅ Combined Server Configured")
logger.info("👉 Web UI: http://0.0.0.0:7860/dev-ui/")
logger.info("👉 MCP SSE: http://0.0.0.0:7860/mcp/sse")

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
