"""
Utility functions for logging and helpers.
"""
import logging
import sys


def setup_logging(level=logging.INFO):
    """
    Setup standard logging configuration.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()
