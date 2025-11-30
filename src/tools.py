"""
Tool definitions for the Legacy Dependency Solver.
Includes Crawl4AI batch crawler for efficient multi-URL processing.
"""
from typing import List, Dict, Any
import json
import sys
import asyncio
import concurrent.futures
from pydantic import BaseModel, Field

from google.adk.tools import FunctionTool
from .utils import logger
from .config import get_memory_service # Import memory service factory

# --- 1. Define Schema (Module level for pickling) ---
class SearchResult(BaseModel):
    relevant_facts: List[str] = Field(..., description="Specific facts/numbers found.")
    summary: str = Field(..., description="Concise summary related to the query.")
    confidence: str = Field(..., description="Confidence level (High/Medium/Low).")

# --- 2. Worker Functions (Run in Subprocess) ---

def _run_batch_crawl_worker(urls: List[str]) -> Dict[str, Any]:
    """
    Worker function to run batch crawl in a separate process.
    """
    # Enforce ProactorEventLoop on Windows for Playwright
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    async def _async_logic():
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        
        # Shared Config
        browser_config = BrowserConfig(
            headless=True,
            ignore_https_errors=True,
            extra_args=["--ignore-certificate-errors", "--ignore-ssl-errors"]
        )
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
        )
        
        results = []
        # limit to top 3
        target_urls = urls[:3]
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for url in target_urls:
                try:
                    crawl_result = await crawler.arun(url=url, config=run_config)
                    if crawl_result.success:
                        results.append(f"--- SOURCE: {url} ---\n{crawl_result.markdown[:15000]}\n")
                    else:
                        results.append(f"--- SOURCE: {url} ---\n[Error: Failed to crawl]\n")
                except Exception as e:
                    results.append(f"--- SOURCE: {url} ---\n[Exception: {str(e)}]\n")
                    
        return {
            "combined_content": "\n".join(results),
            "status": "completed"
        }

    return asyncio.run(_async_logic())


def _run_adaptive_crawl_worker(start_url: str, user_query: str) -> Dict[str, Any]:
    """
    Worker function to run adaptive crawl in a separate process.
    """
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    async def _async_logic():
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, AdaptiveConfig, LLMConfig
        from crawl4ai.extraction_strategy import LLMExtractionStrategy
        
        browser_config = BrowserConfig(
            headless=True,
            verbose=True,
            ignore_https_errors=True,
            extra_args=["--ignore-certificate-errors", "--ignore-ssl-errors"]
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Phase 1: Discovery
            adaptive_config = AdaptiveConfig(
                max_pages=3,
                confidence_threshold=0.7,
                top_k_links=2,
            )
            
            # Import inside function to avoid top-level import issues in subprocess if needed
            from crawl4ai import AdaptiveCrawler
            adaptive = AdaptiveCrawler(crawler, config=adaptive_config)
            
            try:
                await adaptive.digest(start_url=start_url, query=user_query)
            except Exception as e:
                return {"error": f"Crawl failed during discovery: {str(e)}"}
                
            top_content = adaptive.get_relevant_content(top_k=1)
            if not top_content:
                return {"error": "No relevant content found via adaptive crawling."}
                
            best_url = top_content[0]['url']
            
            # Phase 2: Extraction
            dynamic_instruction = f"""
            Extract ONLY information matching this request: '{user_query}'.
            If not found, state that in the summary. Do not hallucinate.
            """
            
            extraction_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=1,
                page_timeout=60000,
                extraction_strategy=LLMExtractionStrategy(
                    llm_config=LLMConfig(provider="ollama/qwen2.5:7b", api_token="ollama"),
                    schema=SearchResult.model_json_schema(),
                    extraction_type="schema",
                    instruction=dynamic_instruction,
                ),
            )
            
            try:
                result = await crawler.arun(url=best_url, config=extraction_config)
                if result.extracted_content:
                    return json.loads(result.extracted_content)
                return {"error": "Extraction returned empty content."}
            except json.JSONDecodeError:
                return {"raw_output": result.extracted_content}
            except Exception as e:
                return {"error": f"Extraction failed: {str(e)}"}

    return asyncio.run(_async_logic())


# --- 3. Main Tools (Async Wrappers) ---

async def batch_crawl_tool(urls: List[str]) -> Dict[str, Any]:
    """
    Crawls a LIST of URLs in one go using a subprocess to ensure correct event loop.
    """
    logger.info(f"🚀 Batch Tool Triggered: Processing {len(urls)} URLs...")
    
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        try:
            result = await loop.run_in_executor(pool, _run_batch_crawl_worker, urls)
            return result
        except Exception as e:
            logger.error(f"❌ Batch crawl subprocess failed: {e}")
            return {"combined_content": f"Error: {str(e)}", "status": "failed"}

async def adaptive_crawl_tool(start_url: str, user_query: str) -> Dict[str, Any]:
    """
    Performs adaptive crawl using a subprocess.
    """
    logger.info(f"🛠️ Tool Triggered: Adaptive Crawl on {start_url}")
    
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        try:
            result = await loop.run_in_executor(pool, _run_adaptive_crawl_worker, start_url, user_query)
            return result
        except Exception as e:
            logger.error(f"❌ Adaptive crawl subprocess failed: {e}")
            return {"error": f"Subprocess failed: {str(e)}"}


# Convert to ADK Tools
batch_tool = FunctionTool(batch_crawl_tool)
adaptive_tool = FunctionTool(adaptive_crawl_tool)


# ===== STATE MANAGEMENT TOOLS =====
from google.adk.tools import ToolContext

def save_context(tool_context: ToolContext, key: str, value: str) -> str:
    tool_context.state[key] = value
    logger.info(f"💾 State Saved: {key} = {value}")
    return f"Saved {key} to state."

def retrieve_context(tool_context: ToolContext, key: str) -> str:
    value = tool_context.state.get(key, "Not found")
    logger.info(f"📂 State Retrieved: {key} = {value}")
    return str(value)

save_context_tool = FunctionTool(save_context)
retrieve_context_tool = FunctionTool(retrieve_context)

def submit_queries(tool_context: ToolContext, queries: List[str]) -> str:
    tool_context.state['search_queries'] = queries
    logger.info(f"🚀 Queries Submitted: {queries}")
    return "Queries submitted successfully."

submit_queries_tool = FunctionTool(submit_queries)

def validate_requirements(tool_context: ToolContext, requirements_content: str) -> str:
    if not requirements_content:
        return "Error: Empty requirements content."
    
    # Relaxed validation for generic dependency files
    # We just check if it has some content and isn't purely whitespace
    if len(requirements_content.strip()) < 5:
         return "Error: Content too short to be a valid dependency file."
         
    logger.info("✅ Dependency file validation passed (Generic check).")
    return "SUCCESS"

validate_tool = FunctionTool(validate_requirements)

# ===== MEMORY RETRIEVAL TOOL =====
async def retrieve_memory(query: str) -> str:
    """
    Searches long-term memory (Pinecone) for relevant past sessions.
    Use this to recall details from previous conversations.
    """
    logger.info(f"🧠 Searching Memory for: {query}")
    try:
        # Initialize service on demand (or use singleton if configured)
        memory_service = get_memory_service()
        results = await memory_service.search_memory(query)
        
        if not results:
            return "No relevant memories found."
            
        formatted_results = "\n---\n".join(results)
        return f"Found relevant memories:\n{formatted_results}"
        
    except Exception as e:
        logger.error(f"❌ Memory retrieval failed: {e}")
        return f"Error retrieving memory: {str(e)}"

retrieve_memory_tool = FunctionTool(retrieve_memory)
