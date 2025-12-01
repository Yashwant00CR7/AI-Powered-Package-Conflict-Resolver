import asyncio
import concurrent.futures
import sys
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Worker Function (Copied from src/tools.py) ---
def _run_batch_crawl_worker(urls: List[str]) -> Dict[str, Any]:
    """
    Worker function to run batch crawl in a separate process.
    """
    print("Worker: Started")
    # Enforce ProactorEventLoop on Windows for Playwright
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    async def _async_logic():
        print("Worker: Importing crawl4ai")
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
        target_urls = urls[:3]
        
        print(f"Worker: Initializing Crawler for {target_urls}")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for url in target_urls:
                try:
                    print(f"Worker: Crawling {url}")
                    crawl_result = await crawler.arun(url=url, config=run_config)
                    if crawl_result.success:
                        results.append(f"--- SOURCE: {url} ---\n{crawl_result.markdown[:500]}\n")
                        print(f"Worker: Success {url}")
                    else:
                        results.append(f"--- SOURCE: {url} ---\n[Error: Failed to crawl]\n")
                        print(f"Worker: Failed {url}")
                except Exception as e:
                    results.append(f"--- SOURCE: {url} ---\n[Exception: {str(e)}]\n")
                    print(f"Worker: Exception {url} - {e}")
                    
        return {
            "combined_content": "\n".join(results),
            "status": "completed"
        }

    return asyncio.run(_async_logic())

# --- Main Test Function ---
async def test_subprocess_crawl():
    urls = ["https://pypi.org/project/requests/"]
    logger.info(f"Main: Starting subprocess test with {urls}")
    
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        try:
            logger.info("Main: Submitting to pool")
            result = await loop.run_in_executor(pool, _run_batch_crawl_worker, urls)
            logger.info("Main: Result received")
            print("\n--- Result ---")
            print(result)
        except Exception as e:
            logger.error(f"Main: Subprocess failed: {e}")

if __name__ == "__main__":
    # Fix for Windows: ProcessPoolExecutor needs this protection
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(test_subprocess_crawl())
