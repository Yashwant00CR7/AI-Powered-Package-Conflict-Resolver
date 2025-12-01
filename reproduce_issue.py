import asyncio
import sys
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Force Proactor on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def test_direct_crawl():
    print("1. Starting direct crawl test...")
    urls = ["https://pypi.org/project/requests/"]
    
    print("2. Configuring Browser...")
    browser_config = BrowserConfig(
        headless=True,
        verbose=True, # Enable verbose logging
        ignore_https_errors=True,
        extra_args=["--ignore-certificate-errors", "--ignore-ssl-errors"]
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
    )
    
    print("3. Initializing AsyncWebCrawler...")
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print("4. Crawler Context Entered.")
            for url in urls:
                print(f"5. Crawling {url}...")
                try:
                    result = await crawler.arun(url=url, config=run_config)
                    print("6. arun() returned.")
                    if result.success:
                        print(f"7. Success! Length: {len(result.markdown)}")
                    else:
                        print(f"7. Failed: {result.error_message}")
                except Exception as e:
                    print(f"7. Exception during crawl: {e}")
    except Exception as e:
        print(f"Error initializing crawler: {e}")
    
    print("8. Done.")

if __name__ == "__main__":
    print("0. Script started.")
    asyncio.run(test_direct_crawl())
