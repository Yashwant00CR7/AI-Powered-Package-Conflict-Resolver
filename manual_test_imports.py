import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force Proactor on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def test_tool_import():
    logger.info("1. Importing batch_tool from src.tools...")
    try:
        from src.tools import batch_tool
        logger.info("2. Import successful.")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return

    urls = ["https://pypi.org/project/requests/"]
    logger.info(f"3. Running batch_tool with {urls}")
    
    try:
        # batch_tool is a FunctionTool, access .func
        result = await batch_tool.func(urls)
        print("\n--- Result ---")
        print(result)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tool_import())
