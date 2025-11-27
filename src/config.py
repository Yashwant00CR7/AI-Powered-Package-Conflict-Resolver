"""
Configuration module for model initialization and environment setup.
CRITICAL: Includes Ollama integration fix for Google ADK.
"""
import os
from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from .utils import logger

# Load environment variables
load_dotenv()

# ===== SSL CONFIGURATION =====
# Fix for SSL certificate errors on Windows
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
logger.info(f"🔐 SSL Cert File configured: {os.environ['SSL_CERT_FILE']}")

# ===== MODEL INITIALIZATION =====
# Using OpenRouter (Grok) via LiteLLM
def get_model():
    """Returns a configured LiteLlm model instance for OpenRouter."""
    # Configure OpenRouter endpoint
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
    
    # Use the requested Grok model
    # LiteLLM uses 'openai/' prefix for OpenAI-compatible endpoints
    model = LiteLlm(model="openai/x-ai/grok-4.1-fast:free")
    
    logger.info("✅ Model initialized: x-ai/grok-4.1-fast:free via OpenRouter")
    return model


# ===== GEMINI MODEL INITIALIZATION =====
# Using Google Gemini for Search Agents
from google.adk.models.google_llm import Gemini
Model="gemini-2.0-flash-lite"
def get_gemini_model():
    """Returns a configured Gemini model instance."""
    model = Gemini(model=Model)
    logger.info(f"✅ Model initialized: {Model}")
    return model


# ===== SESSION SERVICE INITIALIZATION =====
# Using DatabaseSessionService with SQLite + AsyncIO driver
def get_session_service(db_url="sqlite+aiosqlite:///package_conflict_resolver.db"):
    """
    Returns a configured DatabaseSessionService instance.
    
    Args:
        db_url: Database connection string (default: SQLite with aiosqlite driver)
    """
    session_service = DatabaseSessionService(db_url=db_url)
    logger.info(f"✅ Session service initialized: {db_url}")
    return session_service


# ===== MEMORY SERVICE INITIALIZATION =====
# Using InMemoryMemoryService for simplicity (DatabaseMemoryService not available in this ADK version)
from google.adk.memory import InMemoryMemoryService

def get_memory_service():
    """Returns a configured InMemoryMemoryService instance."""
    memory_service = InMemoryMemoryService()
    logger.info("✅ Memory service initialized: InMemory")
    return memory_service
