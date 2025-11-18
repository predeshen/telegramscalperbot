"""
Multi-Symbol Scanner - Main Entry Point
Scans multiple cryptocurrencies and FX pairs simultaneously.
"""
import sys
import os
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime

from src.asset_config_manager import AssetConfigManager
from src.symbol_orchestrator import SymbolOrchestrator
from src.alerter import TelegramAlerter, EmailAlerter, MultiAlerter
from src.signal_diagnostics import SignalDiagnostics
from src.config_validator import ConfigValidator
from src.bypass_mode import BypassMode


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler('logs/multi_symbol_scanner.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def signal_handler(signum, frame, orchestrator):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
    orchestrator.stop()
    sys.exit(0)


def main():
    """Main entry point for multi-symbol scanner."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Multi-Symbol Trading Scanner')
    parser.add_argument(
        '--config',
        type=str,
        default='config/multi_crypto_scalp.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Multi-Symbol Trading Scanner Starting")
    logger.info(f"Configuration: {args.config}")
    logger.info("=" * 80)
    
    try:
        # Load configuration
        config_manager = AssetConfigManager(args.config)
        
        # Display configuration summary
        summary = config_manager.get_config_summary()
        logger.info(f"Configuration loaded: {summary['total_symbols']} symbols, "
                   f"{summary['enabled_symbols']} enabled")
        
        # Initialize diagnostic system
        diagnostics = SignalDiagnostics("Multi-Symbol-Scanner")
        logger.info("Diagnostic system initialized")
        
        # Validate configuration
        validator = ConfigValidator()
        config_dict = config_manager.config  # Get the raw config dict
        warnings = validator.validate_config(config_dict)
        if warnings:
            for warning in warnings:
                logger.warning(f"Config: {warning}")
        
        # Initialize bypass mode
        bypass_mode = BypassMode(config_dict, None)  # Will set alerter later
        
        # Initialize alerter
        # Use environment variables (same as other scanners)
        telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not telegram_bot_token or not telegram_chat_id:
            logger.error("Telegram credentials not found in environment variables!")
            logger.error("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")
            sys.exit(1)
        
        alerter = TelegramAlerter(telegram_bot_token, telegram_chat_id)
        
        if not alerter.enabled:
            logger.error("Telegram alerter not configured properly!")
            sys.exit(1)
        
        # Set alerter for bypass mode
        bypass_mode.alerter = alerter
        
        # Create orchestrator with diagnostics
        orchestrator = SymbolOrchestrator(
            config_manager=config_manager,
            alerter=alerter,
            max_concurrent_symbols=config_manager.get_global_setting('max_concurrent_symbols', 10),
            diagnostics=diagnostics,
            bypass_mode=bypass_mode
        )
        
        # Add all enabled symbols
        enabled_symbols = config_manager.get_enabled_symbols()
        logger.info(f"Adding {len(enabled_symbols)} enabled symbols...")
        
        for symbol in enabled_symbols:
            if orchestrator.add_symbol(symbol):
                logger.info(f"✓ Added {symbol}")
            else:
                logger.warning(f"✗ Failed to add {symbol}")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, orchestrator))
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, orchestrator))
        
        # Start orchestrator
        orchestrator.start()
        
        logger.info("=" * 80)
        logger.info("Multi-Symbol Scanner is now running")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 80)
        
        # Keep main thread alive
        while orchestrator.running:
            import time
            time.sleep(60)
            
            # Monitor symbol health
            orchestrator._monitor_symbol_health()
            
            # Update performance metrics and health check
            orchestrator._update_performance_metrics()
            
            # Periodically log statistics
            stats = orchestrator.get_statistics()
            logger.info(f"Status: {stats['active_threads']} scanners active, "
                       f"{stats['total_signals']} signals ({stats['sent_signals']} sent, "
                       f"{stats['suppressed_signals']} suppressed)")
    
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            orchestrator.stop()
        logger.info("Multi-Symbol Scanner stopped")


if __name__ == "__main__":
    main()
