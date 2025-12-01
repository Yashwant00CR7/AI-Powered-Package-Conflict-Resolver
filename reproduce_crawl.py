import asyncio
import logging
from src.tools import batch_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_batch_crawl():
    urls = ["https://pypi.org/project/requests/"]
    logger.info(f"Testing batch_tool with URLs: {urls}")
    
    try:
        # batch_tool is a FunctionTool, so we access the underlying function via .func
        # Wait, in src/tools.py: batch_tool = FunctionTool(batch_crawl_tool)
        # So batch_tool.func should be the async function batch_crawl_tool
        
        result = await batch_tool.func(urls)
        print("\n--- Result ---")
        print(result)
        
    except Exception as e:
        logger.error(f"Batch tool failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_batch_crawl())
