
# Package Conflict Identifier 📦🔍

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://github.com/google/adk)
[![MCP Ready](https://img.shields.io/badge/MCP-Ready-green.svg)](https://modelcontextprotocol.io/)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Yash030/AI-Package-Doctor)

> **AI-powered package conflict identifier and resolver** using Google's Agent Development Kit (ADK). It leverages a multi-agent architecture with Google Gemini and OpenRouter (Grok) models to diagnose dependency issues, research solutions, and generate fixed configuration files.

<div align="center">

## 🚀 **Try it Live!**

| **Web UI** | **MCP Server Endpoint** |
| :---: | :---: |
| [![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/Yash030/AI-Package-Doctor) | `https://yash030-ai-package-doctor.hf.space/mcp/sse` |

</div>

---

## 🎯 Features

- **🤖 Advanced Multi-Agent Architecture**:
  - **Context Search Agent**: Retrieves insights from past sessions using Pinecone vector memory.
  - **Parallel Research Team**: Concurrent searching of Official Docs and Community forums.
  - **Web Crawl Agent**: Uses **Firecrawl** (via OpenRouter) for deep web scraping of documentation.
  - **Code Surgeon**: Generates and validates `requirements.txt` fixes.

- **🧠 Hybrid Model Intelligence**:
  - **Google Gemini 2.0 Flash Lite**: For high-speed reasoning and orchestration.
  - **Grok 4.1 Fast (via OpenRouter)**: For specialized web crawling and context analysis.

- **🔌 Model Context Protocol (MCP) Server**:
  - Exposes the agent's capabilities as a standard MCP tool (`solve_dependency_issue`).
  - Connects seamlessly to MCP clients like Claude Desktop or other AI assistants.

- **💾 Persistent Memory**:
  - **Short-Term**: SQLite/PostgreSQL session storage.
  - **Long-Term**: Pinecone Vector Database for recalling past solutions.

- **🛠️ Intelligent Tooling**:
  - `retrieve_memory`: Semantic search of previous conversations.
  - `google_search`: Live web search.
  - `firecrawl`: Advanced web scraping.

## 📁 Project Structure

```
package_conflict_resolver/
├── .env                  # Environment variables (API Keys)
├── requirements.txt      # Dependencies
├── main.py               # CLI Entry Point
├── src/
│   ├── combined_server.py # Combined ADK Web UI + MCP Server
│   ├── config.py         # Configuration & Service Initialization
│   ├── tools.py          # Custom Tools (Search, Memory, Validation)
│   ├── agents.py         # Agent Definitions & Workflow
│   └── utils.py          # Logging & Helpers
└── ...
```

## 🏗️ Architecture

<div align="center">
  <img src="https://github.com/user-attachments/assets/ee299a66-8601-494a-a2ba-d102b036dff2" alt="Architecture Diagram" width="800"/>
  <br>
  <em>High-level architecture of the Package Conflict Identifier Agent</em>
</div>

<br>

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd package_conflict_resolver
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your API keys:
```env
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
PINECONE_API_KEY=your_pinecone_key
DATABASE_URL=sqlite+aiosqlite:///legacy_solver.db
```

### 3. Run the Agent

**Option A: Combined Server (Web UI + MCP) - Recommended**
This runs both the ADK Developer UI and the MCP Server on the same port.
```bash
python -m src.combined_server
```
- **Web UI**: [http://localhost:7860/dev-ui/](http://localhost:7860/dev-ui/)
- **MCP SSE Endpoint**: [http://localhost:7860/mcp/sse](http://localhost:7860/mcp/sse)

**Option B: CLI Mode**
```bash
python main.py
```

## 🔌 MCP Server Integration

This agent is deployed as an MCP server, allowing you to use its dependency solving capabilities directly from other AI tools.

### Public Endpoint (Hugging Face Spaces)
- **SSE URL**: `https://yash030-ai-package-doctor.hf.space/mcp/sse`

### Usage with Claude Desktop
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "AI Package Doctor": {
      "command": "",
      "url": "https://yash030-ai-package-doctor.hf.space/mcp/sse",
      "transport": "sse"
    }
  }
}
```

Once connected, you can ask Claude:
> "I have a conflict between numpy 1.26.4 and tensorflow 2.10.0. Can you help me fix it?"

Claude will use the `solve_dependency_issue` tool to analyze the problem using the full power of the agentic workflow.

## 🤖 Agent Workflow

1.  **Query Creator Agent**:
    - Analyzes the user's error message.
    - Uses `retrieve_memory` to check if this issue was solved before.
    - Generates search queries for the research team.

2.  **Context Search Agent**:
    - Specifically looks for relevant context in the project's long-term memory.

3.  **Parallel Research Team**:
    - **Docs Search Agent**: Searches official documentation.
    - **Community Search Agent**: Searches StackOverflow/GitHub.
    - **Web Crawl Agent**: Deep crawls specific documentation pages using Firecrawl.

4.  **Code Surgeon**:
    - Synthesizes all gathered information.
    - Generates a corrected `requirements.txt` or solution plan.

## ☁️ Deployment & Persistence

### Hugging Face Spaces
The project is configured to run on Hugging Face Spaces (Docker SDK).
- **Dockerfile**: Included in the root.
- **Port**: Exposes port `7860`.
- **Storage**: Uses `/data` directory for persistent storage (if configured with persistent volume).

### Database
For production (e.g., Hugging Face Spaces), use a PostgreSQL database:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
```

### Long-Term Memory (Pinecone)
To enable persistent memory across restarts:
1.  Get a free API key from [Pinecone.io](https://www.pinecone.io).
2.  Set `PINECONE_API_KEY` in `.env`.
3.  The agent will automatically index and retrieve past sessions.

## 📝 License

MIT License.

## 🙏 Credits

Built with:
- [Google Agent Development Kit (ADK)](https://github.com/google/adk)
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [OpenRouter](https://openrouter.ai/)
- [Pinecone](https://www.pinecone.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
