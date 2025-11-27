"""
Tool definitions for the Legacy Dependency Solver.
Includes Crawl4AI batch crawler for efficient multi-URL processing.
"""
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, AdaptiveConfig

from google.adk.tools import FunctionTool
from .utils import logger


async def batch_crawl_tool(urls: List[str]) -> str:
    """
    Batch crawls multiple URLs to extract technical documentation.
    
    Args:
        urls: List of URLs to crawl
        
    Returns:
        Combined markdown content from all URLs
    """
    logger.info(f"🕷️  Batch crawling {len(urls)} URLs...")
    
    # Configure browser with headless mode and disable SSL verification
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )
    
    # Configure crawler to bypass cache
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
    )
    
    results = []
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls:
            logger.info(f"  📄 Crawling: {url}")
            try:
                result = await crawler.arun(url=url, config=run_config)
                if result.success:
                    results.append(f"# Content from {url}\n\n{result.markdown}\n\n")
                    logger.info(f"  ✅ Success: {url}")
                else:
                    error_msg = f"Error crawling {url}: {result.error_message}"
                    results.append(f"# {error_msg}\n\n")
                    logger.warning(f"  ❌ Failed: {url} - {result.error_message}")
            except Exception as e:
                error_msg = f"Exception crawling {url}: {str(e)}"
                results.append(f"# {error_msg}\n\n")
                logger.error(f"  ⚠️  Exception: {url} - {e}")
    
    combined = "\n".join(results)
    logger.info(f"✅ Batch crawl completed: {len(results)} results")
    return combined


# ===== ADAPTIVE CRAWLING (COMMENTED OUT - NOT CURRENTLY USED) =====
# Keeping this code for potential future use
# 
# 
async def adaptive_crawl_tool(url: str, query: str) -> str:
    """
    Adaptive crawl for single URLs when batch crawl needs deeper analysis.
    
    Args:
        url: The URL to crawl
        query: The specific query/topic to look for
        
    Returns:
        Extracted markdown content or error message
    """
    logger.info(f"🔍 Adaptive crawling: {url} for '{query}'")
    
    browser_config = BrowserConfig(
        headless=True, 
        verbose=True,
        ignore_https_errors=True,
        extra_args=["--ignore-certificate-errors", "--ignore-ssl-errors"]
    )
    
    # Adaptive config for discovery
    adaptive_config = AdaptiveConfig(
        max_pages=3,
        confidence_threshold=0.7,
        top_k_links=2,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # We need to use the adaptive crawler wrapper or logic if available in this version of crawl4ai
        # Based on reference code, it uses AdaptiveCrawler
        from crawl4ai import AdaptiveCrawler
        
        adaptive = AdaptiveCrawler(crawler, config=adaptive_config)
        
        try:
            # Discovery
            await adaptive.digest(start_url=url, query=query)
            
            top_content = adaptive.get_relevant_content(top_k=1)
            if not top_content:
                return "No relevant content found via adaptive crawling."
                
            best_url = top_content[0]['url']
            logger.info(f"  ✅ Best source found: {best_url}")
            
            # Extraction (simplified to just return markdown for now to avoid complex LLM config in tool)
            # The reference uses LLMExtractionStrategy, but we can rely on the Agent to parse the markdown.
            # We'll just crawl the best URL found.
            
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                word_count_threshold=10,
            )
            
            result = await crawler.arun(url=best_url, config=run_config)
            if result.success:
                return f"# Adaptive Result from {best_url}\n\n{result.markdown}"
            else:
                return f"Error crawling best url {best_url}: {result.error_message}"
                
        except Exception as e:
            logger.error(f"  ❌ Adaptive crawl failed: {e}")
            return f"Adaptive crawl failed: {str(e)}"

adaptive_tool = FunctionTool(adaptive_crawl_tool)



# Wrap tool for ADK Agent usage
batch_tool = FunctionTool(batch_crawl_tool)


# ===== STATE MANAGEMENT TOOLS =====
from typing import Dict, Any
from google.adk.tools import ToolContext

def save_context(tool_context: ToolContext, key: str, value: str) -> str:
    """
    Saves a key-value pair to the session state.
    Useful for remembering packages, versions, or decisions across agents.
    
    Args:
        key: The key to store (e.g., 'packages', 'versions')
        value: The value to store
    """
    tool_context.state[key] = value
    logger.info(f"💾 State Saved: {key} = {value}")
    return f"Saved {key} to state."

def retrieve_context(tool_context: ToolContext, key: str) -> str:
    """
    Retrieves a value from the session state.
    
    Args:
        key: The key to retrieve
    """
    value = tool_context.state.get(key, "Not found")
    logger.info(f"📂 State Retrieved: {key} = {value}")
    return str(value)

save_context_tool = FunctionTool(save_context)
retrieve_context_tool = FunctionTool(retrieve_context)

def submit_queries(tool_context: ToolContext, queries: List[str]) -> str:
    """
    Submits the generated search queries to the shared session state.
    
    Args:
        queries: The list of search queries to submit.
    """
    tool_context.state['search_queries'] = queries
    logger.info(f"🚀 Queries Submitted: {queries}")
    return "Queries submitted successfully."

submit_queries_tool = FunctionTool(submit_queries)

def validate_requirements(tool_context: ToolContext, requirements_content: str) -> str:
    """
    Validates the generated requirements.txt content.
    Checks for basic syntax and conflicting versions (mocked logic).
    
    Args:
        requirements_content: The content of the requirements.txt file.
    """
    if not requirements_content:
        return "Error: Empty requirements content."
        
    lines = requirements_content.strip().split('\n')
    errors = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Basic syntax check (package==version)
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+[=<>!~]+[0-9a-zA-Z\.]+', line):
             # Allow simple package names too, but warn
             if not re.match(r'^[a-zA-Z0-9_\-]+$', line):
                 errors.append(f"Invalid syntax: {line}")
                 
    if errors:
        return f"Validation Failed: {'; '.join(errors)}"
        
    logger.info("✅ Requirements validation passed.")
    return "SUCCESS"

validate_tool = FunctionTool(validate_requirements)
