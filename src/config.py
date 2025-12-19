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
    
    # Use GLM 4.5 Air - free tier optimized for speed with function calling
    # LiteLLM uses 'openai/' prefix for OpenAI-compatible endpoints
    model = LiteLlm(model="openai/z-ai/glm-4.5-air:free")
    
    logger.info("✅ Model initialized: z-ai/glm-4.5-air:free via OpenRouter")
    return model


# ===== GEMINI MODEL INITIALIZATION =====
# Using Google Gemini for Search Agents
from google.adk.models.google_llm import Gemini
Model="gemini-2.5-flash"
def get_gemini_model():
    """Returns a configured Gemini model instance."""
    model = Gemini(model=Model)
    logger.info(f"✅ Model initialized: {Model}")
    return model


# ===== SESSION SERVICE INITIALIZATION =====
# Using LazyDatabaseSessionService to prevent empty sessions on load
from .lazy_session import LazyDatabaseSessionService

def get_session_service(db_url=None):
    """
    Returns a configured DatabaseSessionService instance.
    
    Args:
        db_url: Database connection string. 
                Defaults to DATABASE_URL env var, or local SQLite if not set.
    """
    # Prioritize argument, then env var, then local default
    if not db_url:
        # Use legacy_solver.db as it contains the existing sessions
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///legacy_solver.db")
        
    session_service = LazyDatabaseSessionService(db_url=db_url)
    logger.info(f"✅ Session service initialized (Lazy): {db_url.split('://')[0]}://...") # Log safe URL
    return session_service


# ===== MEMORY SERVICE INITIALIZATION =====
# Using InMemoryMemoryService for simplicity (DatabaseMemoryService not available in this ADK version)
from google.adk.memory import InMemoryMemoryService

# Global cache for memory service
_memory_service_instance = None

def get_memory_service():
    """
    Returns a configured MemoryService instance.
    Uses Pinecone if PINECONE_API_KEY is set, otherwise InMemory.
    Implements Singleton pattern to avoid reloading embeddings.
    """
    global _memory_service_instance
    if _memory_service_instance:
        return _memory_service_instance

    pinecone_key = os.getenv("PINECONE_API_KEY")
    logger.info(f"🔍 Checking PINECONE_API_KEY: {'Found' if pinecone_key else 'Missing'}")
    
    if pinecone_key:
        try:
            from .memory import PineconeMemoryService
            _memory_service_instance = PineconeMemoryService(api_key=pinecone_key)
            logger.info("✅ Memory service initialized: Pinecone (Long-Term Vector Store)")
            return _memory_service_instance
        except Exception as e:
            logger.error(f"❌ Failed to init Pinecone, falling back to InMemory: {e}")
            
    _memory_service_instance = InMemoryMemoryService()
    logger.info("✅ Memory service initialized: InMemory (Ephemeral)")
    return _memory_service_instance
