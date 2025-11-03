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
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector
from src.alerter import TelegramAlerter
from src.trade_tracker import TradeTracker
from src.excel_reporter import ExcelReporter


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
        buffer_size=500
    )
    
    indicator_calc = IndicatorCalculator()
    
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
    
    # Initialize Excel reporter
    excel_reporter = None
    if config.get('excel_reporting', {}).get('enabled', False):
        try:
            smtp_config = config['excel_reporting'].get('smtp', {})
            if smtp_config.get('password') and smtp_config['password'] != 'DISABLED':
                excel_reporter = ExcelReporter(
                    excel_file_path=config['excel_reporting'].get('excel_file_path', 'logs/btc_swing_scans.xlsx'),
                    smtp_config=smtp_config,
                    report_interval_seconds=config['excel_reporting'].get('report_interval_seconds', 3600),
                    initial_report_delay_seconds=config['excel_reporting'].get('initial_report_delay_seconds', 300),
                    scanner_name="BTC Swing Scanner"
                )
                excel_reporter.start()
                logger.info("Excel reporting enabled")
            else:
                logger.warning("Excel reporting disabled: SMTP password not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Excel reporter: {e}")
    
    logger.info("All components initialized successfully")
    
    # Connect to exchange
    logger.info("Connecting to exchange...")
    market_client.connect()
    logger.info(f"Successfully connected to {config['exchange']}")
    
    # Fetch initial data for all timeframes
    candle_data = {}
    for timeframe in config['timeframes']:
        logger.info(f"Fetching initial candlestick data for {timeframe}...")
        candles = market_client.get_latest_candles(timeframe, count=500)
        
        # Calculate indicators
        candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)
        candles['ema_21'] = indicator_calc.calculate_ema(candles, 21)
        candles['ema_50'] = indicator_calc.calculate_ema(candles, 50)
        candles['ema_100'] = indicator_calc.calculate_ema(candles, 100)
        candles['ema_200'] = indicator_calc.calculate_ema(candles, 200)
        candles['vwap'] = indicator_calc.calculate_vwap(candles)
        candles['atr'] = indicator_calc.calculate_atr(candles, 14)
        candles['rsi'] = indicator_calc.calculate_rsi(candles, 14)
        candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, 20)
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
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
                    candles = market_client.get_latest_candles(timeframe, count=500)
                    
                    # Calculate indicators
                    candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)
                    candles['ema_21'] = indicator_calc.calculate_ema(candles, 21)
                    candles['ema_50'] = indicator_calc.calculate_ema(candles, 50)
                    candles['ema_100'] = indicator_calc.calculate_ema(candles, 100)
                    candles['ema_200'] = indicator_calc.calculate_ema(candles, 200)
                    candles['vwap'] = indicator_calc.calculate_vwap(candles)
                    candles['atr'] = indicator_calc.calculate_atr(candles, 14)
                    candles['rsi'] = indicator_calc.calculate_rsi(candles, 14)
                    candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, 20)
                    
                    candle_data[timeframe] = candles
                    
                    # Detect signals
                    signal = signal_detector.detect_signals(candles, timeframe)
                    
                    # Log scan result to Excel
                    if excel_reporter and not candles.empty:
                        last_row = candles.iloc[-1]
                        scan_data = {
                            'timestamp': datetime.now(),
                            'scanner': 'BTC-Swing',
                            'symbol': config['symbol'],
                            'timeframe': timeframe,
                            'price': last_row['close'],
                            'volume': last_row['volume'],
                            'indicators': {
                                'ema_9': last_row.get('ema_9', None),
                                'ema_21': last_row.get('ema_21', None),
                                'ema_50': last_row.get('ema_50', None),
                                'ema_100': last_row.get('ema_100', None),
                                'ema_200': last_row.get('ema_200', None),
                                'rsi': last_row.get('rsi', None),
                                'atr': last_row.get('atr', None),
                                'volume_ma': last_row.get('volume_ma', None),
                                'vwap': last_row.get('vwap', None)
                            },
                            'signal_detected': signal is not None,
                            'signal_type': signal.signal_type if signal else None,
                            'signal_details': {
                                'entry_price': signal.entry_price,
                                'stop_loss': signal.stop_loss,
                                'take_profit': signal.take_profit,
                                'risk_reward': signal.risk_reward,
                                'strategy': getattr(signal, 'strategy', 'EMA Crossover'),
                                'confidence': getattr(signal, 'confidence', None),
                                'market_bias': getattr(signal, 'market_bias', None),
                                'trend_direction': getattr(signal, 'trend_direction', None),
                                'swing_points': getattr(signal, 'swing_points', None),
                                'pullback_depth': getattr(signal, 'pullback_depth', None)
                            } if signal else {}
                        }
                        excel_reporter.log_scan_result(scan_data)
                    
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
                trade_tracker.update_trades(current_price)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Wait before next poll
            time.sleep(config['polling_interval_seconds'])
    
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scanner stopped by user")
        logger.info("=" * 60)
        
        # Stop Excel reporter
        if excel_reporter:
            excel_reporter.stop()
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
