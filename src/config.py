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
from contextvars import ContextVar
from typing import Optional, Any, Dict

# Global context for tracking the current user session
context_user_id: ContextVar[Optional[str]] = ContextVar("context_user_id", default=None)

# Load environment variables
load_dotenv()

# ===== SSL CONFIGURATION =====
# Fix for SSL certificate errors on Windows
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
logger.info(f"SSL Cert File configured: {os.environ['SSL_CERT_FILE']}")

# ===== MODEL INITIALIZATION =====
# Using OpenRouter (Grok) via LiteLLM with Groq Fallback
from google.adk.models.lite_llm import LiteLlm
import asyncio
from typing import AsyncGenerator
import litellm

from google.adk.models.llm_request import LlmRequest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Singleton engine for credential lookups
_cred_engine = None

async def get_user_credentials(user_id: str) -> Dict[str, str]:
    """Fetches custom API keys for the given user from the database."""
    global _cred_engine
    if not user_id:
        return {}
        
    if _cred_engine is None:
        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///legacy_solver.db")
        _cred_engine = create_async_engine(db_url)
        
    try:
        async with _cred_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT gemini_api_key, openrouter_api_key FROM user_credentials WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "gemini_api_key": row[0],
                    "openrouter_api_key": row[1]
                }
    except Exception as e:
        logger.error(f"Error fetching credentials for user {user_id}: {e}")
        
    return {}

class ResilientLiteLlm(LiteLlm):
    """
    A wrapper around LiteLlm that falls back to a secondary model if the primary fails.
    Specifically handles RateLimitErrors with retries and rotation through multiple models.
    """
    def __init__(self, primary_model_names: list[str], fallback_model_name: str = "groq/llama3-70b-8192", **kwargs):
        # Initialize with the first model as default
        super().__init__(model=primary_model_names[0], **kwargs)
        self._primary_models = primary_model_names
        self._fallback_model_name = fallback_model_name
        
        # Ensure Groq API Key is present for fallback
        if not os.getenv("GROQ_API_KEY"):
            logger.warning("GROQ_API_KEY not found. Fallback to Groq will not work.")

    async def generate_content_async(self, contents, **kwargs) -> AsyncGenerator:
        """
        Attempts to generate content with primary models in rotation.
        If a model is rate limited, automatically tries the next one in the list.
        """
        # Auto-wrap string inputs into the LlmRequest structure ADK expects
        if isinstance(contents, str):
            contents = LlmRequest(
                contents=[types.Content(parts=[types.Part(text=contents)])]
            )

        max_retries = 2
        retry_delay = 3

        # Try rotating through primary models
        user_id = context_user_id.get()
        creds = await get_user_credentials(user_id) if user_id else {}
        custom_or_key = creds.get("openrouter_api_key")

        for model_name in self._primary_models:
            self.model = model_name
            
            # Inject custom API key if provided by user
            if custom_or_key:
                kwargs["api_key"] = custom_or_key
                # For LiteLLM to use custom base with custom key correctly
                kwargs["base_url"] = "https://openrouter.ai/api/v1"
            
            for attempt in range(max_retries):
                try:
                    async for chunk in super().generate_content_async(contents, **kwargs):
                        yield chunk
                    return # Success!
                except Exception as e:
                    # Check if it is a rate limit error (429)
                    is_rate_limit = "429" in str(e) or "RateLimitError" in type(e).__name__
                    
                    if is_rate_limit:
                        if attempt < max_retries - 1:
                            logger.warning(f"Model {model_name} rate limited. Retrying in {retry_delay}s... (Attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            continue 
                        else:
                            logger.warning(f"Model {model_name} exhausted. Rotating to next model...")
                            break # Move to next model in the outer loop
                    
                    logger.error(f"Primary model ({model_name}) failed with non-retryable error: {e}")
                    break # Try next model
        
        # Fallback Logic if all primary models fail
        logger.info(f"All primary models exhausted. Switching to fallback: {self._fallback_model_name}")
        self.model = self._fallback_model_name
        
        # Also inject for fallback if applicable (though Groq key is usually system-wide)
        if custom_or_key and self.model.startswith("openrouter/"):
             kwargs["api_key"] = custom_or_key
        
        try:
            async for chunk in super().generate_content_async(contents, **kwargs):
                yield chunk
            logger.info("Fallback successful")
        except Exception as fallback_error:
            logger.error(f"Fallback model ({self._fallback_model_name}) also failed: {fallback_error}")
            raise fallback_error
        finally:
            # Revert model to first primary for next call
            self.model = self._primary_models[0]

def get_model():
    """Returns a configured ResilientLiteLlm model instance with rotation support."""
    # Configure OpenRouter endpoint
    os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
    
    # List of high-performance free models for rotation
    primary_models = [
        """Working Model with tool calling support and no rate limiting"""
        "openrouter/nvidia/nemotron-3-super-120b-a12b:free"
        #Not Working
        # "openrouter/google/gemma-4-26b-a4b-it:free",
        # "openrouter/google/gemma-3-27b-it:free",
        # "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        # "openrouter/qwen/qwen3-coder:free",
    ]
    
    model = ResilientLiteLlm(
        primary_model_names=primary_models,
        fallback_model_name="groq/llama3-70b-8192"
    )
    
    logger.info(f"Model initialized: ResilientLiteLlm (Rotating through: {', '.join(primary_models)})")
    return model


# ===== GEMINI MODEL INITIALIZATION =====
# Using Google Gemini for Search Agents
from google.adk.models.google_llm import Gemini
Model="gemini-2.5-flash"
class ContextAwareGemini(Gemini):
    """
    A wrapper around Gemini that dynamically injects the user's API key
    from the current session context.
    """
    async def generate_content_async(self, contents, **kwargs) -> AsyncGenerator:
        user_id = context_user_id.get()
        if user_id:
            creds = await get_user_credentials(user_id)
            custom_key = creds.get("gemini_api_key")
            if custom_key:
                # Inject custom key into the generate_content call
                # Note: google.genai requires re-initialization of client with the new key
                # or passing it in config if supported. 
                # For google-adk's Gemini class, we need to ensure the underlying client uses it.
                # A robust way is to override the client or re-init property.
                old_key = os.environ.get("GOOGLE_API_KEY")
                try:
                    os.environ["GOOGLE_API_KEY"] = custom_key
                    # Re-initialize the client property if it exists in the ADK Gemini class
                    if hasattr(self, "_client"):
                        self._client = None # Force re-init with new env var
                    async for chunk in super().generate_content_async(contents, **kwargs):
                        yield chunk
                finally:
                    if old_key:
                        os.environ["GOOGLE_API_KEY"] = old_key
                    else:
                        os.environ.pop("GOOGLE_API_KEY", None)
                return

        # Default behavior
        async for chunk in super().generate_content_async(contents, **kwargs):
            yield chunk

def get_gemini_model():
    """Returns a configured ContextAwareGemini model instance."""
    # Ensure Google API Key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found in environment. Gemini may fail.")

    model = ContextAwareGemini(
        model=Model,
        generate_content_config=types.GenerateContentConfig(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(initial_delay=10, attempts=10)
            )
        )
    )
    logger.info(f"Model initialized: {Model} (Context-Aware) with Retry Options")
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
    logger.info(f"Session service initialized (Lazy): {db_url.split('://')[0]}://...") # Log safe URL
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
    logger.info(f"Checking PINECONE_API_KEY: {'Found' if pinecone_key else 'Missing'}")
    
    if pinecone_key:
        try:
            from .memory import PineconeMemoryService
            _memory_service_instance = PineconeMemoryService(api_key=pinecone_key)
            logger.info("Memory service initialized: Pinecone (Long-Term Vector Store)")
            return _memory_service_instance
        except Exception as e:
            logger.error(f"Failed to init Pinecone, falling back to InMemory: {e}")
            
    _memory_service_instance = InMemoryMemoryService()
    logger.info("Memory service initialized: InMemory (Ephemeral)")
    return _memory_service_instance
