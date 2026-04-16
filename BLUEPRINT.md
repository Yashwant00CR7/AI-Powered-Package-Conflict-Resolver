# Project Blueprint

**What we are building:**
An AI-powered Package Conflict Identifier and Resolver (AI-Package-Doctor). This system uses Google's Agent Development Kit (ADK) and a multi-agent architecture (Gemini + Grok) to diagnose, research, and fix Python dependency issues. It also functions as a Model Context Protocol (MCP) server.

**Target Audience:**
- Python Developers dealing with legacy dependency hell.
- DevOps Engineers managing complex environments.
- AI Agents looking for a tool to solve "solve_dependency_issue".

**Core Features:**
- **Hybrid Intelligence**: Utilizes OpenRouter's `openrouter/free` auto-router for high-speed, tool-capable reasoning across multiple free providers.
- **Context Search Agent**: Retrieves solutions from past sessions (Pinecone).
- **Web Crawl Agent**: Deep scraping of documentation via Firecrawl.
- **Code Surgeon Agent**: Generates validated `requirements.txt` fixes.
- **MCP Server**: Exposure of agent capabilities via standard SSE protocol.
- **Web UI**: Developer-friendly interface for manual interaction and debugging.

**Non-negotiable Constraints:**
- **Agentic Integrity**: Every fix MUST be researched and validated via tool-call capable models.
- **Consistency**: Centralized logging and error handling across agents.
- **Resilience**: Use `openrouter/free` to automatically select available models with tool-calling support.
- **Security**: Strict handling of API keys via `.env`.
