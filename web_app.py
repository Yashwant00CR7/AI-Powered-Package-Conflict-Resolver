"""
Web Interface Entry Point for ADK Web UI.
Run with: python web_app.py
"""
import os
import nest_asyncio
import uvicorn
from typing import Optional, Any
from google.adk.cli.adk_web_server import (
    AdkWebServer, BaseAgentLoader, EvalSetsManager, EvalSetResultsManager,
    BaseCredentialService
)
from google.adk.artifacts import FileArtifactService
from src.config import get_session_service, get_memory_service
from src.agents import create_root_agent
from src.utils import logger

# Apply nest_asyncio to handle event loop conflicts
nest_asyncio.apply()

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
        # Dummy implementation: return None or load from file if needed
        # For now, we don't persist credentials, so returning None is safe
        return None

    def save_credential(self, auth_config: Any, callback_context: Any) -> None:
        # Dummy implementation: do nothing
        pass

if __name__ == "__main__":
    logger.info("🌐 Initializing ADK Web Server...")

    # 1. Initialize Services
    session_service = get_session_service()
    memory_service = get_memory_service()
    
    data_dir = os.path.abspath("data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Corrected: use root_dir instead of base_dir
    artifact_service = FileArtifactService(root_dir=os.path.join(data_dir, "artifacts"))
    
    # Use custom LocalCredentialService with implemented abstract methods
    credential_service = LocalCredentialService(base_dir=os.path.join(data_dir, "credentials"))
    
    eval_sets_manager = EvalSetsManager(base_dir=os.path.join(data_dir, "eval_sets"))
    eval_set_results_manager = EvalSetResultsManager(base_dir=os.path.join(data_dir, "eval_results"))

    # 2. Create Agent
    root_agent = create_root_agent()
    agent_loader = SingleAgentLoader(root_agent)

    # 3. Initialize Web Server
    server = AdkWebServer(
        agent_loader=agent_loader,
        session_service=session_service,
        memory_service=memory_service,
        artifact_service=artifact_service,
        credential_service=credential_service,
        eval_sets_manager=eval_sets_manager,
        eval_set_results_manager=eval_set_results_manager,
        agents_dir=os.path.abspath("src")
    )

    # 4. Get FastAPI App
    app = server.get_fast_api_app()

    logger.info("🚀 Starting Server...")
    logger.info("👉 Open: http://127.0.0.1:8000/dev-ui/")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)
