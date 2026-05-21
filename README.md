# Package Conflict Identifier 📦🔍

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://github.com/google/adk)
[![MCP Ready](https://img.shields.io/badge/MCP-Ready-green.svg)](https://modelcontextprotocol.io/)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/Yash030/AI-Package-Doctor)

> AI-powered package conflict identifier and resolver using Google's Agent Development Kit (ADK). A multi-agent architecture with Gemini and Grok models that diagnoses dependency issues, researches solutions, and generates fixed configuration files.

<div align="center">

## 🚀 Try it Live

| **Web UI** | **MCP Server Endpoint** |
| :---: | :---: |
| [![Open in Spaces](https://huggingface.co/datasets/huggingface/badges/resolve/main/open-in-hf-spaces-sm.svg)](https://huggingface.co/spaces/Yash030/AI-Package-Doctor) | `https://yash030-ai-package-doctor.hf.space/mcp/sse` |

</div>

---

## 🎯 Features

- **Multi-Agent Architecture**:
  - **Context Search Agent**: Retrieves insights from past sessions via Pinecone vector memory
  - **Parallel Research Team**: Concurrent search of official docs and community forums
  - **Web Crawl Agent**: Deep scraping via Firecrawl (OpenRouter)
  - **Code Surgeon**: Generates and validates `requirements.txt` fixes

- **Hybrid Model Intelligence**:
  - **Google Gemini 2.0 Flash Lite**: High-speed reasoning and orchestration
  - **Grok via OpenRouter**: Specialized web crawling and context analysis

- **MCP Server**: Exposes `solve_dependency_issue` as a standard MCP tool — connect from Claude Desktop or any MCP client

- **Persistent Memory**:
  - Short-term: SQLite/PostgreSQL session storage
  - Long-term: Pinecone vector DB for recalling past solutions

---

## 🏗️ Architecture

<div align="center">
  <img src="https://github.com/user-attachments/assets/ee299a66-8601-494a-a2ba-d102b036dff2" alt="Architecture Diagram" width="800"/>
</div>

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/Yashwant00CR7/AI-Powered-Package-Conflict-Resolver.git
cd AI-Powered-Package-Conflict-Resolver
pip install -r requirements.txt
```

### 2. Configure Environment
```env
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
PINECONE_API_KEY=your_pinecone_key
DATABASE_URL=sqlite+aiosqlite:///legacy_solver.db
```

### 3. Run

**Combined Server (Web UI + MCP) — recommended:**
```bash
python -m src.combined_server
```
- Web UI: http://localhost:7860/dev-ui/
- MCP SSE: http://localhost:7860/mcp/sse

**CLI mode:**
```bash
python main.py
```

---

## 🔌 MCP Integration

Connect from Claude Desktop by adding to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "AI Package Doctor": {
      "url": "https://yash030-ai-package-doctor.hf.space/mcp/sse",
      "transport": "sse"
    }
  }
}
```

Then ask Claude: *"I have a conflict between numpy 1.26.4 and tensorflow 2.10.0. Can you fix it?"*

---

## 🤖 Agent Workflow

1. **Query Creator** — analyzes error, checks memory for past solutions, generates search queries
2. **Context Search Agent** — semantic search over long-term Pinecone memory
3. **Parallel Research Team** — docs search + community search + Firecrawl deep crawl
4. **Code Surgeon** — synthesizes findings, outputs corrected `requirements.txt`

---

## 📁 Project Structure

```
package_conflict_resolver/
├── main.py               # CLI entry point
├── src/
│   ├── combined_server.py # Web UI + MCP server
│   ├── config.py          # Service initialization
│   ├── tools.py           # Search, memory, validation tools
│   ├── agents.py          # Agent definitions
│   └── utils.py           # Logging & helpers
├── requirements.txt
└── Dockerfile
```

---

## ☁️ Deployment

Runs on Hugging Face Spaces (Docker SDK) on port `7860`. For production, use PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
```

---

## 📝 License

MIT License

## 🙏 Built With

[Google ADK](https://github.com/google/adk) · [Gemini](https://deepmind.google/technologies/gemini/) · [OpenRouter](https://openrouter.ai/) · [Pinecone](https://www.pinecone.io/) · [Model Context Protocol](https://modelcontextprotocol.io/)
