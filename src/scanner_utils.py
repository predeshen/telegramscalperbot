"""
Shared utility functions for all scanners.
Consolidates duplicate code from main entry points.
"""
import logging
import signal
import sys
from pathlib import Path
from typing import Callable, Optional


def setup_logging(log_file: str, log_level: str = "INFO", retention_days: int = 7) -> None:
    """
    Configure logging with file and console handlers.
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        retention_days: Number of days to retain logs
    """
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file} (level={log_level}, retention={retention_days} days)")


def load_json_config(config_path: str) -> dict:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    import json
    with open(config_path, 'r') as f:
        return json.load(f)


def create_signal_handler(shutdown_callback: Optional[Callable] = None) -> Callable:
    """
    Create a signal handler for graceful shutdown.
    
    Args:
        shutdown_callback: Optional callback to execute on shutdown
        
    Returns:
        Signal handler function
    """
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        logger = logging.getLogger(__name__)
        logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
        
        if shutdown_callback:
            try:
                shutdown_callback()
            except Exception as e:
                logger.error(f"Error during shutdown callback: {e}")
        
        sys.exit(0)
    
    return signal_handler


def register_signal_handlers(shutdown_callback: Optional[Callable] = None) -> None:
    """
    Register signal handlers for graceful shutdown.
    
    Args:
        shutdown_callback: Optional callback to execute on shutdown
    """
    handler = create_signal_handler(shutdown_callback)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
