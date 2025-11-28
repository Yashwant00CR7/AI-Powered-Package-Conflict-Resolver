# Package Conflict Identifier 📦🔍

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://github.com/google/adk)

> AI-powered package conflict identifier and resolver using Google's Agent Development Kit (ADK). It leverages a multi-agent architecture with Google Gemini and OpenRouter (Grok) models to diagnose dependency issues, research solutions, and generate fixed configuration files.

## 🎯 Features

- **Advanced Multi-Agent Architecture**:
  - **Context Search Agent**: Retrieves insights from past sessions using Pinecone vector memory.
  - **Parallel Research Team**: Concurrent searching of Official Docs and Community forums.
  - **Web Crawl Agent**: Uses **Firecrawl** (via OpenRouter) for deep web scraping of documentation.
  - **Code Surgeon**: Generates and validates `requirements.txt` fixes.
- **Hybrid Model Intelligence**:
  - **Google Gemini 2.0 Flash Lite**: For high-speed reasoning and orchestration.
  - **Grok 4.1 Fast (via OpenRouter)**: For specialized web crawling and context analysis.
- **Persistent Memory**:
  - **Short-Term**: SQLite/PostgreSQL session storage.
  - **Long-Term**: Pinecone Vector Database for recalling past solutions.
- **Intelligent Tooling**:
  - `retrieve_memory`: Semantic search of previous conversations.
  - `google_search`: Live web search.
  - `firecrawl`: Advanced web scraping.

## 📁 Project Structure

```
package_conflict_resolver/
├── .env                  # Environment variables (API Keys)
├── requirements.txt      # Dependencies
├── main.py               # CLI Entry Point
├── web_app.py            # Web UI Entry Point (ADK Web Server)
└── src/
    ├── __init__.py
    ├── config.py         # Configuration & Service Initialization
    ├── tools.py          # Custom Tools (Search, Memory, Validation)
    ├── agents.py         # Agent Definitions & Workflow
    └── utils.py          # Logging & Helpers
```

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

**Option A: CLI Mode (Recommended for quick tasks)**
```bash
python main.py
```

**Option B: Web UI (Full Experience)**
```bash
adk web --no-reload
```
Open [http://127.0.0.1:8000/dev-ui/](http://127.0.0.1:8000/dev-ui/) to interact with the agent visually and view chat history.

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
