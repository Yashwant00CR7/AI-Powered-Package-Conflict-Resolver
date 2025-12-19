"""Legacy Dependency Solver - Modular Package"""

# from .agents import root_agent # Removed to prevent side-effects
from .config import get_session_service, get_memory_service

# Initialize services for ADK to discover
session_service = get_session_service()
memory_service = get_memory_service()

__all__ = ["session_service", "memory_service"]
