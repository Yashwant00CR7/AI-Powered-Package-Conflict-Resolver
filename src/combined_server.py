"""
Combined Server for AI-Package-Doctor.
Runs both the ADK Web UI and the MCP Server on the same FastAPI app.
"""
import os
import sys
import asyncio

# CRITICAL: Set event loop policy BEFORE any other imports
# Fix for Playwright on Windows with nest_asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
import nest_asyncio
from fastapi import FastAPI, Request, Header
from fastapi.responses import RedirectResponse
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

from src.config import get_session_service, get_memory_service, context_user_id
from src.agents import create_root_agent
from src.utils import logger
from typing import Optional, Any
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

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

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    # Set context-aware user_id for BYOK key injection
    # In MCP context, we use a fixed user or extract from session if possible
    # For now, default to mcp_user
    context_user_id.set("mcp_user")
    
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
                    # Log event author for debugging
                    author = getattr(event, 'author', 'unknown')
                    logger.info(f"📨 Event received from: {author}")

                    # FILTER: Only return output from the final agent (Code_Surgeon_Agent)
                    if author == "Code_Surgeon_Agent":
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

# Add routes directly to the FastAPI app
app.add_route("/mcp/sse", handle_sse, methods=["GET"])
app.add_route("/mcp/messages", handle_messages, methods=["POST"])

@app.get("/")
async def root():
    return RedirectResponse(url="/dev-ui/")

# --- 6. BYOK Settings Page ---

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(user_id: str = "mcp_user"):
    """Serves the premium BYOK settings page."""
    # Fetch existing keys
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///legacy_solver.db")
    engine = create_async_engine(db_url)
    gemini_key = ""
    openrouter_key = ""
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT gemini_api_key, openrouter_api_key FROM user_credentials WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                gemini_key = row[0] or ""
                openrouter_key = row[1] or ""
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
    finally:
        await engine.dispose()

    # Premium HTML Design
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI-Package-Doctor | Settings</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
                --card-bg: rgba(30, 41, 59, 0.7);
                --accent-primary: #6366f1;
                --accent-secondary: #0ea5e9;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --glass-border: rgba(255, 255, 255, 0.1);
            }}

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
            }}

            body {{
                background: var(--bg-gradient);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--text-main);
                overflow: hidden;
            }}

            .container {{
                width: 100%;
                max-width: 500px;
                padding: 2rem;
                position: relative;
            }}

            .glass-card {{
                background: var(--card-bg);
                backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border);
                border-radius: 24px;
                padding: 3rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
            }}

            @keyframes slideUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            .header {{
                text-align: center;
                margin-bottom: 2.5rem;
            }}

            .header h1 {{
                font-size: 2rem;
                font-weight: 600;
                background: linear-gradient(to right, #6366f1, #0ea5e9);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }}

            .header p {{
                color: var(--text-muted);
                font-size: 0.9rem;
            }}

            .form-group {{
                margin-bottom: 1.5rem;
                position: relative;
            }}

            .form-group label {{
                display: block;
                margin-bottom: 0.5rem;
                font-size: 0.85rem;
                color: var(--text-muted);
                font-weight: 400;
            }}

            .form-group input {{
                width: 100%;
                background: rgba(15, 23, 42, 0.5);
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                padding: 1rem;
                color: white;
                font-size: 0.95rem;
                transition: all 0.3s ease;
                outline: none;
            }}

            .form-group input:focus {{
                border-color: var(--accent-primary);
                box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
                background: rgba(15, 23, 42, 0.8);
            }}

            .btn-save {{
                width: 100%;
                background: linear-gradient(to right, var(--accent-primary), var(--accent-secondary));
                color: white;
                border: none;
                border-radius: 12px;
                padding: 1.1rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-top: 1rem;
                box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
            }}

            .btn-save:hover {{
                transform: translateY(-2px);
                box-shadow: 0 15px 20px -3px rgba(99, 102, 241, 0.5);
            }}

            .btn-save:active {{
                transform: scale(0.98);
            }}

            .footer-links {{
                text-align: center;
                margin-top: 2rem;
                font-size: 0.8rem;
            }}

            .footer-links a {{
                color: var(--text-muted);
                text-decoration: none;
                transition: color 0.2s;
            }}

            .footer-links a:hover {{
                color: var(--accent-secondary);
            }}

            .toast {{
                position: fixed;
                bottom: 2rem;
                left: 50%;
                transform: translateX(-50%);
                background: #10b981;
                color: white;
                padding: 1rem 2rem;
                border-radius: 50px;
                font-weight: 600;
                opacity: 0;
                transition: opacity 0.3s, transform 0.3s;
                z-index: 1000;
            }}

            .toast.show {{
                opacity: 1;
                transform: translate(-50%, -10px);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="glass-card">
                <div class="header">
                    <h1>AI Provider Keys</h1>
                    <p>Bring Your Own Keys (BYOK)</p>
                </div>
                
                <form id="settingsForm">
                    <input type="hidden" name="user_id" value="{user_id}">
                    <div class="form-group">
                        <label for="gemini_api_key">Google Gemini API Key</label>
                        <input type="password" id="gemini_api_key" name="gemini_api_key" placeholder="Enter your Gemini key..." value="{gemini_key}">
                    </div>
                    
                    <div class="form-group">
                        <label for="openrouter_api_key">OpenRouter API Key</label>
                        <input type="password" id="openrouter_api_key" name="openrouter_api_key" placeholder="Enter your OpenRouter key..." value="{openrouter_key}">
                    </div>
                    
                    <button type="submit" class="btn-save">Save Credentials</button>
                </form>

                <div class="footer-links">
                    <a href="/dev-ui/">← Back to Dashboard</a>
                </div>
            </div>
        </div>

        <div id="toast" class="toast">Settings Saved Successfully!</div>

        <script>
            document.getElementById('settingsForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                
                try {{
                    const response = await fetch('/settings/save', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    
                    if (response.ok) {{
                        const toast = document.getElementById('toast');
                        toast.classList.add('show');
                        setTimeout(() => toast.classList.remove('show'), 3000);
                    }} else {{
                        alert('Failed to save settings.');
                    }}
                }} catch (error) {{
                    console.error('Error:', error);
                    alert('An error occurred.');
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content

from pydantic import BaseModel
class SettingsUpdate(BaseModel):
    user_id: str
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

@app.post("/settings/save")
async def save_settings(data: SettingsUpdate):
    """Saves the API keys to the database."""
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///legacy_solver.db")
    engine = create_async_engine(db_url)
    
    try:
        async with engine.begin() as conn:
            # UPSERT logic for user_credentials
            await conn.execute(text("""
                INSERT INTO user_credentials (user_id, gemini_api_key, openrouter_api_key, updated_at)
                VALUES (:user_id, :gemini_api_key, :openrouter_api_key, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    gemini_api_key = EXCLUDED.gemini_api_key,
                    openrouter_api_key = EXCLUDED.openrouter_api_key,
                    updated_at = EXCLUDED.updated_at
            """), {
                "user_id": data.user_id,
                "gemini_api_key": data.gemini_api_key,
                "openrouter_api_key": data.openrouter_api_key
            })
            logger.info(f"✅ Credentials updated for user: {data.user_id}")
            return {{"status": "success"}}
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return {{"status": "error", "message": str(e)}}
    finally:
        await engine.dispose()

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
