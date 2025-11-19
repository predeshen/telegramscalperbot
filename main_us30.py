"""
US30 Aggressive Momentum Scanner
Designed to catch big directional moves with FVG and structure breaks
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
from src.us30_strategy import US30Strategy
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.alerter import TelegramAlerter
from src.trade_tracker import TradeTracker
from src.excel_reporter import ExcelReporter
from src.signal_diagnostics import SignalDiagnostics
from src.config_validator import ConfigValidator
from src.bypass_mode import BypassMode


def setup_logging(log_file: str, log_level: str) -> None:
    """Configure logging with file and console handlers."""
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
    logger.info(f"Logging initialized: {log_file} (level={log_level})")


def load_config(config_path: str = "config/us30_config.json") -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    """Main scanner loop for US30 momentum trading."""
    # Register signal handlers
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
    logger.info("US30 AGGRESSIVE MOMENTUM SCANNER")
    logger.info("Strategy: FVG + Structure Breaks + Momentum")
    logger.info(f"Timeframes: {', '.join(config['timeframes'])}")
    logger.info("=" * 60)
    
    # Initialize diagnostic system
    diagnostics = SignalDiagnostics("US30-Momentum")
    logger.info("Diagnostic system initialized")
    
    # Validate configuration
    validator = ConfigValidator()
    warnings = validator.validate_config(config)
    if warnings:
        for warning in warnings:
            logger.warning(f"Config: {warning}")
    
    # Initialize bypass mode
    bypass_mode = BypassMode(config, None)  # Will set alerter later
    
    # Initialize components
    market_client = YFinanceClient(
        symbol=config['symbol'],
        timeframes=config['timeframes'],
        buffer_size=500
    )
    
    indicator_calc = IndicatorCalculator()
    
    # Initialize US30 strategy
    us30_strategy = US30Strategy(config=config)
    
    # Initialize alerter
    alerter = None
    if config['telegram']['enabled']:
        bot_token = config['telegram'].get('bot_token') or os.getenv(config['telegram'].get('bot_token_env', ''))
        chat_id = config['telegram'].get('chat_id') or os.getenv(config['telegram'].get('chat_id_env', ''))
        
        if bot_token and chat_id:
            alerter = TelegramAlerter(bot_token, chat_id)
            logger.info("Telegram alerter initialized")
        else:
            logger.warning("Telegram credentials not found")
    
    # Set alerter for bypass mode
    bypass_mode.alerter = alerter
    
    # Initialize quality filter
    quality_filter_config = config.get('quality_filter', {})
    quality_config = QualityConfig(
        min_confluence_factors=quality_filter_config.get('min_confluence_factors', 3),
        min_confidence_score=quality_filter_config.get('min_confidence_score', 3),
        duplicate_window_seconds=quality_filter_config.get('duplicate_window_seconds', 600),
        duplicate_price_tolerance_pct=quality_filter_config.get('duplicate_price_tolerance_pct', 1.0),
        significant_price_move_pct=quality_filter_config.get('significant_price_move_pct', 1.5),
        min_risk_reward=quality_filter_config.get('min_risk_reward', 1.2)
    )
    quality_filter = SignalQualityFilter(quality_config, diagnostics=diagnostics)
    logger.info("Signal Quality Filter initialized")
    
    # Initialize trade tracker
    trade_tracker = TradeTracker(alerter=alerter)
    
    # Initialize Excel reporter
    excel_reporter = None
    if config.get('excel_reporting', {}).get('enabled', False):
        try:
            smtp_config = config['excel_reporting'].get('smtp', {})
            if smtp_config.get('password') and smtp_config['password'] != 'DISABLED':
                excel_reporter = ExcelReporter(
                    excel_file_path=config['excel_reporting'].get('excel_file_path', 'logs/us30_momentum_scans.xlsx'),
                    smtp_config=smtp_config,
                    report_interval_seconds=config['excel_reporting'].get('report_interval_seconds', 3600),
                    initial_report_delay_seconds=config['excel_reporting'].get('initial_report_delay_seconds', 300),
                    scanner_name="US30 Momentum Scanner"
                )
                excel_reporter.start()
                logger.info("Excel reporting enabled")
        except Exception as e:
            logger.error(f"Failed to initialize Excel reporter: {e}")
    
    logger.info("All components initialized successfully")
    
    # Connect to data source
    logger.info("Connecting to Yahoo Finance...")
    market_client.connect()
    logger.info(f"Successfully connected for {config['symbol']}")
    
    # Fetch initial data
    candle_data = {}
    for timeframe in config['timeframes']:
        logger.info(f"Fetching initial data for {timeframe}...")
        candles, is_fresh = market_client.get_latest_candles(timeframe, count=500, validate_freshness=False)
        
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
        candles['adx'] = indicator_calc.calculate_adx(candles, period=14)
        
        # Calculate Stochastic
        stoch_k, stoch_d = indicator_calc.calculate_stochastic(candles, k_period=14, d_period=3, smooth_k=3)
        candles['stoch_k'] = stoch_k
        candles['stoch_d'] = stoch_d
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
    # Send startup notification
    if alerter:
        try:
            df = candle_data[config['timeframes'][0]]
            current_price = df.iloc[-1]['close'] if not df.empty else 0
            
            startup_msg = (
                f"🚀 <b>US30 Momentum Scanner Started</b>\n\n"
                f"💰 Current Price: ${current_price:,.2f}\n"
                f"⏰ Timeframes: {', '.join(config['timeframes'])}\n"
                f"🎯 Strategy: FVG + Structure Breaks\n"
                f"📊 Min ADX: {config.get('us30_strategy', {}).get('min_adx', 25)}\n"
                f"🎯 Target: {config.get('us30_strategy', {}).get('initial_tp_atr', 2.5)} ATR\n\n"
                f"🔍 Hunting for big moves..."
            )
            alerter.send_message(startup_msg)
        except Exception as e:
            logger.warning(f"Failed to send startup message: {e}")
    
    # Main polling loop
    logger.info(f"Starting main polling loop ({config['polling_interval_seconds']}-second intervals)...")
    logger.info("Scanner is now running. Press Ctrl+C to stop.")
    
    last_heartbeat = time.time()
    heartbeat_interval = 5400  # 90 minutes
    
    try:
        while True:
            # Update data for each timeframe
            for timeframe in config['timeframes']:
                try:
                    # Fetch latest candles (disable freshness validation)
                    candles, is_fresh = market_client.get_latest_candles(timeframe, count=500, validate_freshness=False)
                    
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
                    candles['adx'] = indicator_calc.calculate_adx(candles, period=14)
                    
                    stoch_k, stoch_d = indicator_calc.calculate_stochastic(candles, k_period=14, d_period=3, smooth_k=3)
                    candles['stoch_k'] = stoch_k
                    candles['stoch_d'] = stoch_d
                    
                    candle_data[timeframe] = candles
                    
                    # Detect signals using US30 strategy
                    detected_signal = us30_strategy.detect_signal(candles, timeframe)
                    
                    # Log scan result to Excel
                    if excel_reporter and not candles.empty:
                        last_row = candles.iloc[-1]
                        
                        scan_data = {
                            'timestamp': datetime.now(),
                            'scanner': 'US30-Momentum',
                            'symbol': config['symbol'],
                            'timeframe': timeframe,
                            'price': last_row['close'],
                            'volume': last_row['volume'],
                            'indicators': {
                                'ema_50': last_row.get('ema_50', None),
                                'rsi': last_row.get('rsi', None),
                                'atr': last_row.get('atr', None),
                                'adx': last_row.get('adx', None),
                                'volume_ma': last_row.get('volume_ma', None)
                            },
                            'signal_detected': detected_signal is not None,
                            'signal_type': detected_signal.signal_type if detected_signal else None,
                            'signal_details': {
                                'entry_price': detected_signal.entry_price,
                                'stop_loss': detected_signal.stop_loss,
                                'take_profit': detected_signal.take_profit,
                                'risk_reward': detected_signal.risk_reward,
                                'strategy': detected_signal.strategy,
                                'confidence': detected_signal.confidence,
                                'reasoning': detected_signal.reasoning
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
                    
                    indicators = {
                        'rsi': last_candle.get('rsi', 50),
                        'prev_rsi': prev_candle.get('rsi', 50),
                        'adx': last_candle.get('adx', 0),
                        'volume_ratio': last_candle['volume'] / last_candle['volume_ma'] if last_candle.get('volume_ma', 0) > 0 else 0
                    }
                    
                    trade_tracker.update_trades(current_price, indicators)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Heartbeat
            current_time = time.time()
            if current_time - last_heartbeat >= heartbeat_interval:
                try:
                    df = candle_data[config['timeframes'][0]]
                    if not df.empty:
                        last_candle = df.iloc[-1]
                        heartbeat_msg = (
                            f"💙 <b>US30 Scanner Heartbeat</b>\n\n"
                            f"⏰ Time: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                            f"💰 Price: ${last_candle['close']:,.2f}\n"
                            f"📊 ADX: {last_candle.get('adx', 0):.1f}\n"
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
        
        if excel_reporter:
            excel_reporter.stop()
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
