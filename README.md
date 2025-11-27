# AI-Powered Package Conflict Resolver 🤖🔧

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4.svg)](https://github.com/google/adk)

> AI-powered package conflict resolver using Google's Agent Development Kit with intelligent dependency analysis and web crawling capabilities.

## 🎯 Features

- **Advanced Multi-Agent Architecture**:
  - **Parallel Agents**: Concurrent research gathering from Official Docs and Community sources
  - **Loop Agents**: Self-correcting code generation with automated verification
  - **Custom Agents**: Deterministic fallback logic for robust web crawling
- **Google Gemini Integration**: Uses `gemini-2.0-flash-lite` for high-speed reasoning and function calling
- **State Management**: Persistent session storage with context-aware package tracking
- **Intelligent Tooling**:
  - `submit_queries`: Structured output handling
  - `validate_requirements`: Automated syntax verification
  - `save_context`: Cross-agent state persistence

## 📁 Project Structure

```
package_conflict_resolver/
├── .env                  # Environment variables (Google API Key)
├── requirements.txt      # Dependencies
├── main.py               # Entry point (CLI execution)
└── src/
    ├── __init__.py
    ├── config.py         # Model initialization & Database Memory Service
    ├── tools.py          # Crawl4AI, Validation, & Context tools
    ├── agents.py         # Agent definitions (Sequential, Parallel, Loop, Custom)
    └── utils.py          # Logging and helper functions
```

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd package_conflict_resolver

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install browser for crawler
crawl4ai-setup

# 4. Configure your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 5. Run the agent
python main.py
```

## 🤖 Agent Workflow

1. **Query Creator Agent**: 
   - Analyzes the error log and extracts package names.
   - Saves package context to persistent memory.
   - Generates targeted search queries.

2. **Parallel Research Team** (ParallelAgent):
   - **Docs Search Agent**: Scours official documentation (*.org, *.io).
   - **Community Search Agent**: Checks StackOverflow and GitHub Issues.
   - Runs concurrently for maximum efficiency.

3. **Web Crawl Agent** (CustomAgent):
   - Deterministically attempts fast batch crawling first.
   - Automatically falls back to adaptive crawling if data is insufficient.

4. **Code Surgeon Team** (LoopAgent):
   - **Code Surgeon**: Generates `requirements.txt` based on research.
   - **Verification Agent**: Validates syntax and conflicts.
   - **Stop Checker**: Loops the process until verification passes (Self-Correction).

## 🐛 Troubleshooting

### API Key Errors
Ensure `GOOGLE_API_KEY` is correctly set in `.env`.

### SSL/Certificate errors
The crawler has SSL verification disabled by default. If issues persist, check your firewall settings.

### Database locked errors
Ensure only one instance of the application is running at a time.

## ☁️ Deployment & Persistence

To ensure your agent's memory (sessions) survives restarts on platforms like **Hugging Face Spaces** or **Google Cloud Run**, you must use an external database.

1.  **Get a Free PostgreSQL Database**: Use a provider like [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), or [CockroachDB](https://www.cockroachlabs.com).
2.  **Get the Connection String**: It looks like `postgresql://user:password@host/dbname`.
3.  **Set Environment Variable**:
    - In your deployment settings (Secrets/Variables), add:
      ```env
      DATABASE_URL=postgresql://user:password@host/dbname
      ```
    - The app will automatically detect this and switch from local SQLite to your cloud database.

### 🧠 Long-Term Memory (Pinecone)

To enable persistent memory search (so the agent remembers past conversations after restart):

1.  **Get a Free Pinecone API Key**: Sign up at [Pinecone.io](https://www.pinecone.io).
2.  **Create an Index** (Optional - code does it automatically):
    - Name: `adk-memory`
    - Dimensions: `384`
    - Metric: `cosine`
3.  **Set Environment Variable**:
    ```env
    PINECONE_API_KEY=your_pinecone_api_key
    ```
    The agent will automatically switch to `PineconeMemoryService`.

## 📝 License

MIT License - feel free to use in your own projects!

## 🙏 Credits

Built with:
- [Google Agent Development Kit (ADK)](https://github.com/google/adk)
- [Google Gemini](https://deepmind.google/technologies/gemini/)
- [Crawl4AI](https://github.com/unclecode/crawl4ai)

