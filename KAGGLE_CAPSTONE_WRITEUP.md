# Package Conflict Identifier 📦🔍
**Why "Chatting with AI" Isn't Enough for Modern Debugging**

---

## The Problem: "Lazy AI" vs. Real-World Bugs

We've all been there. You paste a cryptic error message into ChatGPT or Gemini, and it gives you a confident, generic answer: *"Check your syntax"* or *"Ensure your JSON is formatted correctly."*

But what if your syntax is fine? What if the error isn't in *your* code, but deep inside a library you just installed? What if it's a brand-new bug reported on GitHub only 48 hours ago?

**Static LLMs fail here because they are frozen in time.** They don't know about the bug report filed yesterday. They don't know that `library-v2.1` broke compatibility with `framework-v3.0`. They guess based on general patterns, often leading you down a rabbit hole of useless "fixes."

I built the **Package Conflict Identifier** to solve this. It doesn't just "guess"—it **investigates**.

---

## The "Real Web" Advantage

This isn't just a chatbot. It's an autonomous research team. When it sees an error, it doesn't rely solely on its training data. It:
1.  **Diagnoses** the specific package causing the issue.
2.  **Searches** the live web for that specific error string.
3.  **Crawls** GitHub Issues, StackOverflow, and official documentation.
4.  **Synthesizes** a solution based on *current* reality, not 2023 data.

### Case Study: The "Ollama/LiteLLM" Bug

During development, I encountered a nasty error while trying to chain agents using **LiteLLM** and **Ollama**:

```text
litellm.APIConnectionError: Ollama_chatException - {"error":"json: cannot unmarshal array into Go struct field ChatRequest.messages.content of type string"}
```

#### ❌ The Generic AI Answer (ChatGPT/Gemini)
When I pasted this into a standard LLM, it said:
> *"You are sending an array instead of a string in your JSON request. Change your code to send a string."*

This was **useless**. I wasn't writing the raw JSON request; the `litellm` library was. I couldn't "just change my code."

#### ✅ The Agent's Answer
My **Package Conflict Identifier** took a different approach.
1.  **Query Creator** generated search terms: `"LiteLLM Ollama json unmarshal array error"`.
2.  **Docs Search Agent** found a specific GitHub Issue: **`BerriAI/litellm#11148`**.
3.  **Web Crawl Agent** read the issue thread and found the root cause:
    > *"LiteLLM sends content as an array/object (OpenAI-style), but Ollama expects a simple string. This is a known incompatibility in LiteLLM v1.66+."*

**The Result:** Instead of wasting hours debugging my own code, the agent told me: *"This is a bug in the library. Downgrade LiteLLM or apply this specific patch."*

**This is the difference between a chatbot and an engineer.**

---

## System Architecture

How does it work? It uses a multi-agent pipeline to mimic a senior engineer's debugging workflow.

```text
User Input (Error Log)
      |
      V
+----------------------------------+
| PHASE 1: DIAGNOSIS               |
| Query Creator Agent              |
| (Consults Pinecone Memory)       |
+----------------------------------+
      |
      V
+----------------------------------+
| PHASE 2: RESEARCH                |
| Parallel Research Team:          |
| 1. Docs Search Agent             |
| 2. Community Search Agent        |
| 3. Web Crawl Agent (Firecrawl)   |
+----------------------------------+
      |
      V
+----------------------------------+
| PHASE 3: REPAIR                  |
| Code Surgeon Team:               |
| [Surgeon] -> [Verify] -> [Fix]   |
+----------------------------------+
      |
      V
Output (Fixed requirements.txt)
```

### Detailed Component Breakdown

#### 1. Phase 1: Contextual Diagnosis (The Detective)
The entry point is the **Query Creator Agent**, powered by **Gemini 2.0 Flash Lite**. We chose Flash Lite for its speed and low latency. This agent also has access to **Pinecone Vector Memory**. Before searching the web, it queries the vector database: *"Have we seen this error before?"* This "Long-Term Memory" allows the system to get smarter over time, instantly recalling fixes for recurring issues without re-doing the research.

#### 2. Phase 2: The Parallel Research Engine (The Researchers)
Research is time-consuming. To optimize this, we use the **ParallelAgent** pattern. Two agents run simultaneously:
*   **Docs Search Agent**: Uses Google Search API restricted to domains like `readthedocs.io`, `docs.python.org`, and `pypi.org`. It looks for the "official" way things should work.
*   **Community Search Agent**: Restricted to `stackoverflow.com` and `github.com/issues`. It looks for the "hacky" workarounds and bug reports.

#### 3. Phase 3: Deep Web Extraction (The Crawler)
Standard search tools only give you snippets. To truly understand a bug, you need to read the code. We integrated **Firecrawl**, a specialized tool for turning websites into LLM-ready markdown. When the researchers find a promising URL (like a GitHub commit diff), the **Web Crawl Agent** (powered by **Grok** via OpenRouter) visits the page, renders the JavaScript, and extracts the raw text. Grok was chosen here for its massive context window (128k+ tokens), allowing it to ingest entire documentation pages in one go.

#### 4. Phase 4: The Self-Correcting Loop (The Surgeon)
The final phase is the **Code Surgeon**. It proposes a fix (e.g., a new `requirements.txt`). But instead of just outputting it, it enters a **Validation Loop**.
1.  **Surgeon** generates the file.
2.  **Verification Agent** (a separate model instance) acts as a "Linter." It checks: *Does this version exist? Are there obvious conflicts?*
3.  If the check fails, the Surgeon is reprimanded and forced to try again.
This "System 2 Thinking" loop significantly reduces the rate of hallucinated package versions.

---

## Technology Stack

*   **Orchestration**: Google Agent Development Kit (ADK)
*   **Reasoning**: Google Gemini 2.0 Flash Lite (Speed) & Grok (Context)
*   **Web Intelligence**: Firecrawl (Deep Scraping) & Google Search API
*   **Memory**: Pinecone (Long-term Vector Storage) & SQLite (Session History)

## Conclusion

The future of coding isn't just "auto-complete." It's **auto-debug**. By giving LLMs access to the live web and structuring them into specialized agents, we can solve the complex, library-internal bugs that generic chatbots simply can't touch.

**GitHub**: [https://github.com/Yashwant00CR7/AI-Powered-Package-Conflict-Resolver]
**Built with**: Google ADK, Gemini, Grok, Firecrawl
