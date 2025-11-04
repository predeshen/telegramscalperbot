"""
Multi-Timeframe BTC Scanner for Swing Trading
Monitors 15m, 1h, 4h, and 1d timeframes for longer-term signals
"""
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from src.yfinance_client import YFinanceClient
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


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    """Main scanner loop for swing trading timeframes."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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
    logger.info(f"Data Source: Yahoo Finance ({config['symbol']})")
    logger.info(f"Timeframes: {', '.join(config['timeframes'])}")
    logger.info("=" * 60)
    
    # Initialize components
    # Use YFinance for better data quality (especially volume)
    market_client = YFinanceClient(
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
    
    # Configure H4 HVG if enabled
    if config.get('h4_hvg', {}).get('enabled', False):
        signal_detector.configure_h4_hvg(config['h4_hvg'], config['symbol'])
        logger.info("H4 HVG detection enabled for BTC swing trading")
    
    # Initialize alerter
    alerter = None
    if config['telegram']['enabled']:
        # Try direct values first, then environment variables
        bot_token = config['telegram'].get('bot_token') or os.getenv(config['telegram'].get('bot_token_env', ''))
        chat_id = config['telegram'].get('chat_id') or os.getenv(config['telegram'].get('chat_id_env', ''))
        
        if bot_token and chat_id:
            alerter = TelegramAlerter(bot_token, chat_id)
            logger.info("Telegram alerter initialized")
        else:
            logger.warning("Telegram credentials not found in config or environment variables")
    
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
    
    # Connect to data source
    logger.info("Connecting to Yahoo Finance...")
    market_client.connect()
    logger.info(f"Successfully connected to Yahoo Finance for {config['symbol']}")
    
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
        
        # Calculate Stochastic
        stoch_k, stoch_d = indicator_calc.calculate_stochastic(candles, k_period=14, d_period=3, smooth_k=3)
        candles['stoch_k'] = stoch_k
        candles['stoch_d'] = stoch_d
        
        # Calculate ADX
        candles['adx'] = indicator_calc.calculate_adx(candles, period=14)
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
    # Send startup notification
    if alerter:
        try:
            # Get current price from first timeframe
            df = candle_data[config['timeframes'][0]]
            current_price = df.iloc[-1]['close'] if not df.empty else 0
            ema_200 = df.iloc[-1].get('ema_200', 0) if not df.empty else 0
            
            startup_msg = (
                f"🟢 <b>BTC Swing Scanner Started</b>\n\n"
                f"💰 Current Price: ${current_price:,.2f}\n"
                f"📊 EMA 200: ${ema_200:,.2f}\n"
                f"📈 Primary Trend: {'Bullish' if current_price > ema_200 else 'Bearish'}\n"
                f"⏰ Timeframes: {', '.join(config['timeframes'])}\n"
                f"🎯 Strategy: Trend Following + EMA Crossovers\n\n"
                f"🔍 Scanning for swing opportunities..."
            )
            alerter.send_message(startup_msg)
        except Exception as e:
            logger.warning(f"Failed to send startup message: {e}")
    
    # Main polling loop
    logger.info(f"Using polling mode for data updates (more reliable across exchanges)...")
    logger.info("Scanner is now running. Press Ctrl+C to stop.")
    logger.info(f"Starting main polling loop ({config['polling_interval_seconds']}-second intervals)...")
    
    # Track last heartbeat time
    last_heartbeat = time.time()
    heartbeat_interval = 5400  # 90 minutes in seconds
    
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
                    
                    # Calculate Stochastic
                    stoch_k, stoch_d = indicator_calc.calculate_stochastic(candles, k_period=14, d_period=3, smooth_k=3)
                    candles['stoch_k'] = stoch_k
                    candles['stoch_d'] = stoch_d
                    
                    # Calculate ADX
                    candles['adx'] = indicator_calc.calculate_adx(candles, period=14)
                    
                    candle_data[timeframe] = candles
                    
                    # Detect signals
                    detected_signal = signal_detector.detect_signals(candles, timeframe)
                    
                    # Log scan result to Excel
                    if excel_reporter and not candles.empty:
                        last_row = candles.iloc[-1]
                        # Determine scanner name based on strategy
                        scanner_name = 'BTC-Swing'
                        if detected_signal and getattr(detected_signal, 'strategy', '') == 'H4 HVG':
                            scanner_name = 'BTC-Swing-H4HVG'
                        
                        scan_data = {
                            'timestamp': datetime.now(),
                            'scanner': scanner_name,
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
                            'signal_detected': detected_signal is not None,
                            'signal_type': detected_signal.signal_type if detected_signal else None,
                            'signal_details': {
                                'entry_price': detected_signal.entry_price,
                                'stop_loss': detected_signal.stop_loss,
                                'take_profit': detected_signal.take_profit,
                                'risk_reward': detected_signal.risk_reward,
                                'strategy': getattr(detected_signal, 'strategy', 'EMA Crossover'),
                                'confidence': getattr(detected_signal, 'confidence', None),
                                'market_bias': getattr(detected_signal, 'market_bias', None),
                                'trend_direction': getattr(detected_signal, 'trend_direction', None),
                                'swing_points': getattr(detected_signal, 'swing_points', None),
                                'pullback_depth': getattr(detected_signal, 'pullback_depth', None),
                                'gap_size_percent': getattr(detected_signal, 'gap_info', {}).gap_percent if detected_signal and hasattr(detected_signal, 'gap_info') and detected_signal.gap_info else None,
                                'volume_spike_ratio': getattr(detected_signal, 'volume_spike_ratio', None) if detected_signal else None,
                                'confluence_factors': len(getattr(detected_signal, 'confluence_factors', [])) if detected_signal and hasattr(detected_signal, 'confluence_factors') and detected_signal.confluence_factors else None
                            } if detected_signal else {}
                        }
                        excel_reporter.log_scan_result(scan_data)
                    
                    if detected_signal:
                        logger.info(f"🚨 {detected_signal.signal_type} SIGNAL on {timeframe}!")
                        logger.info(f"Entry: ${detected_signal.entry_price:.2f}, SL: ${detected_signal.stop_loss:.2f}, TP: ${detected_signal.take_profit:.2f}")
                        logger.info(f"Confidence: {detected_signal.confidence}/5, R:R = {detected_signal.risk_reward:.2f}")
                        
                        # Send alert
                        if alerter:
                            alerter.send_signal_alert(detected_signal)
                        
                        # Track trade
                        trade_tracker.add_trade(detected_signal)
                
                except Exception as e:
                    logger.error(f"Error processing {timeframe}: {e}")
            
            # Check for trade updates
            try:
                df = candle_data[config['timeframes'][0]]
                if not df.empty and len(df) >= 2:
                    last_candle = df.iloc[-1]
                    prev_candle = df.iloc[-2]
                    current_price = last_candle['close']
                    
                    # Prepare indicators for TP extension logic
                    indicators = {
                        'rsi': last_candle.get('rsi', 50),
                        'prev_rsi': prev_candle.get('rsi', 50),
                        'adx': last_candle.get('adx', 0),
                        'volume_ratio': last_candle['volume'] / last_candle['volume_ma'] if last_candle.get('volume_ma', 0) > 0 else 0
                    }
                    
                    trade_tracker.update_trades(current_price, indicators)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Check if it's time for heartbeat message (every 15 minutes)
            current_time = time.time()
            if current_time - last_heartbeat >= heartbeat_interval:
                try:
                    # Get latest data for heartbeat
                    df = candle_data[config['timeframes'][0]]
                    if not df.empty:
                        last_candle = df.iloc[-1]
                        heartbeat_msg = (
                            f"💙 <b>BTC Swing Scanner Heartbeat</b>\n\n"
                            f"⏰ Time: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                            f"💰 Price: ${last_candle['close']:,.2f}\n"
                            f"📊 EMA 200: ${last_candle.get('ema_200', 0):,.2f}\n"
                            f"📈 RSI: {last_candle.get('rsi', 0):.1f}\n"
                            f"🔍 Status: Actively scanning..."
                        )
                        alerter.send_message(heartbeat_msg)
                        last_heartbeat = current_time
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat: {e}")
            
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
