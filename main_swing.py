"""
Multi-Timeframe BTC Scanner for Swing Trading
Monitors 15m, 1h, 4h, and 1d timeframes for longer-term signals
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from src.market_data_client import MarketDataClient
from src.signal_detector import SignalDetector
from src.alerter import TelegramAlerter
from src.trade_tracker import TradeTracker


def setup_logging(log_file: str, log_level: str) -> None:
    """Configure logging with file and console handlers."""
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine retention days
    retention_days = 30
    
    # Configure root logger
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


def load_config(config_path: str = "config/config_multitime.json") -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main scanner loop for swing trading timeframes."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(
        config['logging']['file'],
        config['logging']['level']
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("BTC Swing Trading Scanner Starting")
    logger.info(f"Timeframes: {', '.join(config['timeframes'])}")
    logger.info("=" * 60)
    
    # Initialize components
    market_client = MarketDataClient(
        exchange_name=config['exchange'],
        symbol=config['symbol'],
        timeframes=config['timeframes'],
        buffer_size=200
    )
    
    signal_detector = SignalDetector(
        volume_spike_threshold=config['signal_detection']['volume_spike_threshold'],
        rsi_min=config['signal_detection']['rsi_min'],
        rsi_max=config['signal_detection']['rsi_max'],
        stop_loss_atr_multiplier=config['signal_detection']['stop_loss_atr_multiplier'],
        take_profit_atr_multiplier=config['signal_detection']['take_profit_atr_multiplier'],
        duplicate_time_window_minutes=config['signal_detection']['duplicate_time_window_minutes'],
        duplicate_price_threshold_percent=config['signal_detection']['duplicate_price_threshold_percent']
    )
    
    # Initialize alerter
    alerter = None
    if config['telegram']['enabled']:
        bot_token = os.getenv(config['telegram']['bot_token_env'])
        chat_id = os.getenv(config['telegram']['chat_id_env'])
        
        if bot_token and chat_id:
            alerter = TelegramAlerter(bot_token, chat_id)
        else:
            logger.warning("Telegram credentials not found in environment variables")
    
    # Initialize trade tracker
    trade_tracker = TradeTracker(alerter=alerter)
    
    logger.info("All components initialized successfully")
    
    # Connect to exchange
    logger.info("Connecting to exchange...")
    market_client.connect()
    logger.info(f"Successfully connected to {config['exchange']}")
    
    # Fetch initial data for all timeframes
    candle_data = {}
    for timeframe in config['timeframes']:
        logger.info(f"Fetching initial candlestick data for {timeframe}...")
        candles = market_client.get_latest_candles(timeframe, count=200)
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data")
    
    # Main polling loop
    logger.info(f"Using polling mode for data updates (more reliable across exchanges)...")
    logger.info("Scanner is now running. Press Ctrl+C to stop.")
    logger.info(f"Starting main polling loop ({config['polling_interval_seconds']}-second intervals)...")
    
    try:
        while True:
            # Update data for each timeframe
            for timeframe in config['timeframes']:
                try:
                    # Fetch latest candles
                    candles = market_client.get_latest_candles(timeframe, count=200)
                    candle_data[timeframe] = candles
                    
                    # Detect signals
                    signal = signal_detector.detect_signals(candles, timeframe)
                    
                    if signal:
                        logger.info(f"🚨 {signal.signal_type} SIGNAL on {timeframe}!")
                        logger.info(f"Entry: ${signal.entry_price:.2f}, SL: ${signal.stop_loss:.2f}, TP: ${signal.take_profit:.2f}")
                        logger.info(f"Confidence: {signal.confidence}/5, R:R = {signal.risk_reward:.2f}")
                        
                        # Send alert
                        if alerter:
                            alerter.send_signal_alert(signal)
                        
                        # Track trade
                        trade_tracker.add_trade(signal)
                
                except Exception as e:
                    logger.error(f"Error processing {timeframe}: {e}")
            
            # Check for trade updates
            try:
                current_price = candle_data[config['timeframes'][0]].iloc[-1]['close']
                updates = trade_tracker.check_for_updates(current_price)
                
                for update in updates:
                    logger.info(f"📊 Trade Update: {update['message']}")
                    if alerter:
                        alerter.send_trade_update(update)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Wait before next poll
            time.sleep(config['polling_interval_seconds'])
    
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scanner stopped by user")
        logger.info("=" * 60)
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
