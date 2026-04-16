# Architecture

Define folder structures, routing conventions, and dependencies.

**Project Structure:**
- `/src`: Core application logic.
  - `agents.py`: Multi-agent orchestration and individual agent logic.
  - `tools.py`: Specialized toolsets for search, crawling, and memory.
  - `config.py`: Centralized service initialization (DB, Pinecone, LLM).
  - `combined_server.py`: FastAPI-based integration of ADK UI and MCP.
  - `memory.py`: Vector database management.
- `/ui`: Custom UI components (if any) or configuration for ADK UI.
- `/data`: Persistent storage for SQLite and temporary files.

**Key Dependencies:**
- `google-adk`: Agent framework.
* `litellm`: Multi-provider LLM support via `openrouter/free`.
- `pinecone`: Long-term memory.
- `fastapi` & `mcp`: Server and communication protocol.
- `crawl4ai` / `firecrawl`: Web intelligence.
