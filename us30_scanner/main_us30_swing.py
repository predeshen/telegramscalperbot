"""
US30 (Dow Jones) Swing Trading Scanner
Multi-day position trading with trend continuation and reversal strategies
"""
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.yfinance_client import YFinanceClient
from src.indicator_calculator import IndicatorCalculator
from src.alerter import TelegramAlerter
from src.trade_tracker import TradeTracker
from src.excel_reporter import ExcelReporter

from us30_scanner.us30_swing_detector import US30SwingDetector


def setup_logging(log_file: str, log_level: str) -> None:
    """Configure logging."""
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
    logger.info(f"Logging initialized: {log_file}")


def load_config(config_path: str = "us30_scanner/config_us30_swing.json") -> dict:
    """Load configuration."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main US30 swing scanner loop."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(
        config['logging']['file'],
        config['logging']['level']
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("US30 Swing Trading Scanner Starting")
    logger.info("=" * 60)
    
    # Initialize components
    logger.info("Initializing components...")
    
    market_client = YFinanceClient(
        symbol=config['exchange']['symbol'],
        timeframes=config['exchange']['timeframes'],
        buffer_size=200
    )
    
    indicator_calc = IndicatorCalculator()
    
    signal_detector = US30SwingDetector(config=config['signal_rules'])
    
    # Initialize alerter
    alerter = None
    if config['telegram']['enabled']:
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']
        
        if bot_token and chat_id:
            alerter = TelegramAlerter(bot_token, chat_id)
            logger.info("Telegram alerter initialized")
        else:
            logger.warning("Telegram credentials not found")
    
    # Initialize trade tracker
    trade_tracker = TradeTracker(alerter=alerter)
    
    # Initialize Excel reporter
    excel_reporter = None
    if config.get('excel_reporting', {}).get('enabled', False):
        try:
            smtp_config = config['excel_reporting'].get('smtp', {})
            if smtp_config.get('password') and smtp_config['password'] != 'DISABLED':
                excel_reporter = ExcelReporter(
                    excel_file_path=config['excel_reporting'].get('excel_file_path', 'logs/us30_swing_scans.xlsx'),
                    smtp_config=smtp_config,
                    report_interval_seconds=config['excel_reporting'].get('report_interval_seconds', 3600),
                    initial_report_delay_seconds=config['excel_reporting'].get('initial_report_delay_seconds', 300),
                    scanner_name="US30 Swing Scanner"
                )
                excel_reporter.start()
                logger.info("Excel reporting enabled")
            else:
                logger.warning("Excel reporting disabled: SMTP password not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Excel reporter: {e}")
    
    logger.info("All components initialized successfully")
    
    # Connect to data source
    logger.info(f"Connecting to {config['exchange']['name']}...")
    if not market_client.connect():
        logger.error("Failed to connect to data source")
        sys.exit(1)
    
    logger.info(f"Successfully connected to {config['exchange']['name']}")
    
    # Fetch initial data
    logger.info("Fetching initial data...")
    candle_data = {}
    for timeframe in config['exchange']['timeframes']:
        candles = market_client.get_latest_candles(timeframe, count=500)
        
        # Calculate indicators
        candles['ema_21'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_fast'])
        candles['ema_50'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_momentum'])
        candles['ema_200'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_trend'])
        candles['atr'] = indicator_calc.calculate_atr(candles, config['indicators']['atr_period'])
        candles['rsi'] = indicator_calc.calculate_rsi(candles, config['indicators']['rsi_period'])
        candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, config['indicators']['volume_ma_period'])
        
        # Calculate MACD
        macd, macd_signal, macd_histogram = indicator_calc.calculate_macd(
            candles,
            config['indicators']['macd_fast'],
            config['indicators']['macd_slow'],
            config['indicators']['macd_signal']
        )
        candles['macd'] = macd
        candles['macd_signal'] = macd_signal
        candles['macd_histogram'] = macd_histogram
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
    # Send startup notification
    if alerter:
        current_price = candle_data[config['exchange']['timeframes'][0]].iloc[-1]['close']
        ema_200 = candle_data[config['exchange']['timeframes'][0]].iloc[-1]['ema_200']
        trend = "Bullish" if current_price > ema_200 else "Bearish"
        
        alerter.send_message(
            f"🟢 <b>US30 Swing Scanner Started</b>\n\n"
            f"💰 Current Price: {current_price:,.2f}\n"
            f"📊 EMA 200: {ema_200:,.2f}\n"
            f"📈 Primary Trend: {trend}\n"
            f"⏰ Timeframes: {', '.join(config['exchange']['timeframes'])}\n"
            f"🎯 Strategy: Trend Continuation + Reversals\n\n"
            f"🔍 Scanning for swing opportunities..."
        )
    
    logger.info("Scanner is now running. Press Ctrl+C to stop.")
    
    # Track last check times to avoid duplicate signals
    last_check_times = {tf: None for tf in config['exchange']['timeframes']}
    last_heartbeat = time.time()
    heartbeat_interval = 900  # 15 minutes in seconds
    
    try:
        while True:
            # Update data for each timeframe
            for timeframe in config['exchange']['timeframes']:
                try:
                    # Determine check interval based on timeframe
                    check_intervals = {
                        '4h': 14400,  # 4 hours
                        '1d': 86400   # 1 day
                    }
                    
                    interval = check_intervals.get(timeframe, 3600)
                    
                    # Check if we should scan this timeframe
                    current_time = datetime.now()
                    last_check = last_check_times[timeframe]
                    
                    if last_check is None or (current_time - last_check).total_seconds() >= interval:
                        # Fetch latest candles
                        candles = market_client.get_latest_candles(timeframe, count=500)
                        
                        # Calculate indicators
                        candles['ema_21'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_fast'])
                        candles['ema_50'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_momentum'])
                        candles['ema_200'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_trend'])
                        candles['atr'] = indicator_calc.calculate_atr(candles, config['indicators']['atr_period'])
                        candles['rsi'] = indicator_calc.calculate_rsi(candles, config['indicators']['rsi_period'])
                        candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, config['indicators']['volume_ma_period'])
                        
                        # Calculate MACD
                        macd, macd_signal, macd_histogram = indicator_calc.calculate_macd(
                            candles,
                            config['indicators']['macd_fast'],
                            config['indicators']['macd_slow'],
                            config['indicators']['macd_signal']
                        )
                        candles['macd'] = macd
                        candles['macd_signal'] = macd_signal
                        candles['macd_histogram'] = macd_histogram
                        
                        candle_data[timeframe] = candles
                        
                        # Detect signals
                        signal = signal_detector.detect_signals(candles, timeframe)
                        
                        # Log scan result to Excel
                        if excel_reporter and not candles.empty:
                            last_row = candles.iloc[-1]
                            scan_data = {
                                'timestamp': datetime.now(),
                                'scanner': 'US30-Swing',
                                'symbol': config['exchange']['symbol'],
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
                            logger.info(f"Strategy: {signal.strategy}")
                            logger.info(f"Entry: {signal.entry_price:.2f}, SL: {signal.stop_loss:.2f}, TP: {signal.take_profit:.2f}")
                            logger.info(f"R:R = {signal.risk_reward:.2f}")
                            
                            # Send alert
                            if alerter:
                                alerter.send_signal_alert(signal)
                            
                            # Track trade
                            trade_tracker.add_trade(signal)
                        
                        # Update last check time
                        last_check_times[timeframe] = current_time
                
                except Exception as e:
                    logger.error(f"Error processing {timeframe}: {e}")
            
            # Check for trade updates
            try:
                current_price = candle_data[config['exchange']['timeframes'][0]].iloc[-1]['close']
                trade_tracker.update_trades(current_price)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Check if it's time for heartbeat message (every 15 minutes)
            current_time = time.time()
            if current_time - last_heartbeat >= heartbeat_interval:
                try:
                    # Get latest data for heartbeat
                    df = candle_data[config['exchange']['timeframes'][0]]
                    if not df.empty:
                        last_candle = df.iloc[-1]
                        heartbeat_msg = (
                            f"🤍 <b>US30 Swing Scanner Heartbeat</b>\n\n"
                            f"⏰ Time: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                            f"💰 Price: {last_candle['close']:,.2f}\n"
                            f"📊 EMA 200: {last_candle.get('ema_200', 0):,.2f}\n"
                            f"📈 RSI: {last_candle.get('rsi', 0):.1f}\n"
                            f"🔍 Status: Actively scanning..."
                        )
                        alerter.send_message(heartbeat_msg)
                        last_heartbeat = current_time
                except Exception as e:
                    logger.warning(f"Failed to send heartbeat: {e}")
            
            # Sleep
            time.sleep(config['polling_interval_seconds'])
    
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scanner stopped by user")
        logger.info("=" * 60)
        
        # Stop Excel reporter
        if excel_reporter:
            excel_reporter.stop()
        
        # Send shutdown notification
        if alerter:
            alerter.send_message("🔴 <b>US30 Swing Scanner Stopped</b>\n\nScanner has been shut down.")
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        
        if alerter:
            alerter.send_message(f"❌ <b>Scanner Error</b>\n\nFatal error occurred. Check logs.")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
