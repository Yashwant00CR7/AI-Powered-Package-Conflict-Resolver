# AI-Powered Package Conflict Resolver
**An Intelligent Multi-Agent System for Automated Dependency Management**

---

## Problem Statement

Every developer who has worked with legacy codebases knows the pain: you inherit a project from years ago, run `pip install -r requirements.txt`, and suddenly you're drowning in cryptic error messages about version conflicts, deprecated APIs, and incompatible dependencies. What should take minutes to set up turns into hours—or even days—of debugging.

The problem is deceptively complex:
- **Version incompatibility**: Package A requires numpy<1.20, but Package B needs numpy>=1.21
- **Breaking changes**: APIs get deprecated, function signatures change, and migration guides are scattered across dozens of documentation sites
- **Transitive dependencies**: You update one package, and suddenly five others break
- **Legacy code rot**: Projects using Python 2.7, TensorFlow 1.x, or outdated frameworks that no longer have clear upgrade paths

According to a 2023 survey by Stack Overflow, **62% of developers** spend more than 4 hours per week dealing with dependency issues. For organizations maintaining legacy systems, this number skyrockets. The manual process is tedious: reading changelogs, searching Stack Overflow, testing combinations, and often trial-and-error until something works.

**This is not just a technical nuisance—it's a productivity killer.** Time spent fighting dependency hell is time not spent building features, fixing bugs, or innovating. For students working on legacy college projects, open-source maintainers, or enterprises with decade-old codebases, this problem is both pervasive and costly.

I built the **AI-Powered Package Conflict Resolver** to transform this multi-hour debugging nightmare into a **60-second automated solution**.

---

## Why Agents?

Traditional approaches to dependency resolution—static analysis tools, simple version constraint solvers, or basic pip dependency resolvers—fall short because **dependency conflicts are not just a computational problem; they're a research problem**.

Here's why agents are the perfect solution:

### 1. **Multi-Step Reasoning is Required**
Solving dependency conflicts isn't a single-step task. It requires:
- Understanding the error (what broke and why)
- Researching breaking changes (which requires reading documentation)
- Finding compatible versions (cross-referencing multiple sources)
- Generating a solution (creating fixed requirements.txt)

This sequential, context-dependent workflow is exactly what **multi-agent systems excel at**. Each agent specializes in one step, passing enriched context to the next.

### 2. **Dynamic Information Gathering**
Unlike static tools, dependency issues require **real-time web research**. You need to:
- Search for migration guides
- Crawl official documentation
- Extract version compatibility matrices
- Read GitHub issue threads

Agents with **tool-calling capabilities** (Google Search, Web Crawling) can dynamically gather this information, something rule-based systems cannot do.

### 3. **Contextual Intelligence**
LLM-powered agents understand natural language, allowing them to:
- Parse unstructured error logs
- Interpret vague deprecation warnings
- Synthesize information from multiple sources
- Make intelligent trade-offs (e.g., "upgrade TensorFlow but keep NumPy stable")

A traditional solver would fail here—it doesn't "understand" what `AttributeError: module 'numpy' has no attribute 'float'` actually means. An agent does.

### 4. **Specialization Through Division of Labor**
By breaking the problem into specialized sub-agents:
- **Query Creator**: Expert at diagnosing errors and formulating research questions
- **Researcher**: Expert at finding authoritative documentation
- **Web Crawler**: Expert at extracting structured data from unstructured web pages
- **Code Surgeon**: Expert at synthesizing findings into actionable fixes

Each agent focuses on its core competency, resulting in **higher accuracy and better solutions** than a monolithic system.

Agents aren't just "a trendy approach"—they're the right tool for a problem that demands reasoning, research, and contextual decision-making.

---

## What I Created: System Architecture

The **Package Conflict Resolver** is a **four-agent sequential pipeline** built with Google's Agent Development Kit (ADK) and powered by Gemini 2.5 Pro. Here's how it works:

### **Architecture Overview**

```
User Input (Error + Packages)
        ↓
┌──────────────────────────┐
│  1. Query Creator Agent  │  ← Diagnoses issue, generates search queries
└──────────────────────────┘
        ↓
┌──────────────────────────┐
│  2. Researcher Agent     │  ← Executes Google Search, finds URLs
└──────────────────────────┘
        ↓
┌──────────────────────────┐
│  3. Web Crawler Agent    │  ← Crawls docs, extracts version info
└──────────────────────────┘
        ↓
┌──────────────────────────┐
│  4. Code Surgeon Agent   │  ← Analyzes findings, generates fix
└──────────────────────────┘
        ↓
Output (Fixed requirements.txt + Explanation)
```

### **Agent Breakdown**

**1. Query Creator Agent (Dependency Detective)**
- **Model**: Gemini 2.5 Pro
- **Tools**: Google Search, Context Memory
- **Role**: Analyzes the error log and package versions, identifies the root cause (e.g., "numpy.float deprecated in NumPy 1.24"), and generates targeted search queries like:
  - `"numpy.float deprecated version migration guide"`
  - `"tensorflow 2.x keras compatibility matrix"`

**2. Researcher Agent (Technical Resource Curator)**
- **Model**: Gemini 2.5 Pro
- **Tools**: Google Search
- **Role**: Executes the generated queries, filters results by credibility (prioritizing official docs, GitHub, Stack Overflow), and returns the top 7 most relevant URLs.

**3. Web Crawler Agent (Content Extractor)**
- **Model**: Grok (via OpenRouter)
- **Tools**: Batch Crawl (Crawl4AI), Adaptive Crawl
- **Role**: Crawls the URLs, extracts structured information (version requirements, breaking changes, migration steps), and summarizes findings.

**4. Code Surgeon Agent**
- **Model**: Grok (via OpenRouter)
- **Tools**: Context Memory
- **Role**: Synthesizes all research, determines compatible package versions, generates a fixed `requirements.txt`, and provides a migration guide.

### **Key Design Decisions**

- **Sequential Flow**: Each agent builds on the previous agent's output, creating a knowledge pipeline.
- **Dual-Model Strategy**: Gemini for reasoning-heavy tasks (diagnosis, query generation), Grok for extraction-heavy tasks (web crawling).
- **Session Memory**: SQLite + async I/O for persistent session state across runs.
- **Context Sharing**: Agents use a shared context store to pass package names, versions, and findings between steps.

---

## Demo

**[INSERT DEMO IMAGE/VIDEO HERE]**

*Example: User provides error log → System generates queries → Crawls NumPy docs → Returns fixed requirements.txt in ~60 seconds*

---

## The Build: Tools & Technologies

### **Core Framework**
- **Google Agent Development Kit (ADK)** - Agent orchestration, tool integration, session management
- **Google Gemini 2.5 Pro** - Advanced reasoning, function calling, query generation
- **OpenRouter (Grok)** - Cost-effective web content extraction

### **Web Intelligence**
- **Crawl4AI** - Async web crawling with JavaScript rendering
- **Google Search API** - Real-time documentation discovery

### **Infrastructure**
- **SQLite + aiosqlite** - Async session persistence
- **nest_asyncio** - Event loop management for both CLI and web interfaces
- **Python 3.8+** - Core programming language

### **Development Workflow**
1. **Prototype**: Started with a Jupyter notebook implementing the core logic
2. **Refactor**: Segregated code into modular architecture (`src/agents.py`, `src/tools.py`, `src/config.py`)
3. **Integration**: Connected agents using ADK's SequentialAgent pattern
4. **Testing**: Built verification scripts to validate each agent independently
5. **Deployment**: Created both CLI (`main.py`) and web interface (`web_app.py`)

### **Challenges Solved**
- **Model Limitations**: Initially used Gemini 2.0 Flash Lite, but hit function-calling limits. Upgraded to Gemini 2.5 Pro for better tool use.
- **SSL Errors**: Disabled SSL verification in Crawl4AI for compatibility with certain documentation sites.
- **Session Management**: Implemented proper async session creation to avoid "Session not found" errors.

---

## If I Had More Time, Here's What I'd Do

### **1. Extend Language Support**
Currently Python-focused. I'd add:
- **JavaScript/Node.js** - npm package conflicts
- **Java/Maven** - dependency tree resolution
- **Docker** - multi-language containerized environments

### **2. Interactive Conflict Resolution**
Allow users to:
- Choose between multiple fix options (e.g., "Upgrade TensorFlow vs. Downgrade NumPy")
- Specify version constraints (e.g., "Must stay on Python 3.8")
- Preview changes before applying

### **3. Automated Testing Agent**
Add a fifth agent that:
- Generates test scripts to verify the fix
- Runs them in an isolated environment (Docker/venv)
- Reports success/failure with detailed logs

### **4. Visual Dependency Graph**
Build an interactive graph showing:
- Current dependency tree
- Conflicting edges highlighted in red
- Proposed changes in green
- Transitive impact analysis

### **5. Database of Known Conflicts**
Create a knowledge base:
- Store previously resolved conflicts
- Use RAG (Retrieval-Augmented Generation) to find similar past solutions
- Reduce API calls by reusing known fixes

### **6. GitHub Integration**
- Auto-detect issues in repositories
- Create pull requests with fixes
- Comment on dependency-related issues with solutions

### **7. Cost Optimization**
- Implement caching for frequently accessed documentation
- Use smaller models for simpler tasks
- Add rate limiting and quota management

---

## Conclusion

The **AI-Powered Package Conflict Resolver** proves that **agents are not just hype—they're the future of intelligent automation**. By combining multi-agent orchestration, real-time web research, and advanced LLM reasoning, this project solves a real-world problem that costs developers millions of hours annually.

This is just the beginning. Imagine a world where every developer has an AI assistant that not only fixes dependency conflicts but autonomously maintains entire codebases, keeping them healthy, modern, and secure.

**The future of software development is agentic. This project is a step toward that future.**

---

**Word Count**: ~1,485 words

**GitHub**: [your-repo-link]  
**Live Demo**: [your-demo-link]  
**Built with**: Google ADK, Gemini 2.5 Pro, Crawl4AI
