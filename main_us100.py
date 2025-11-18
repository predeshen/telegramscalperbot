"""
US100/NASDAQ Scanner
Monitors NASDAQ-100 index for trading signals using multiple strategies including H4-HVG
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


def load_config(config_path: str = "config/us100_config.json") -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


def main():
    """Main scanner loop for US100/NASDAQ."""
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
    logger.info("US100/NASDAQ Scanner Starting")
    logger.info(f"Symbol: {config['symbol']}")
    logger.info(f"Timeframes: {', '.join(config['timeframes'])}")
    logger.info("=" * 60)
    
    # Initialize diagnostic system
    diagnostics = SignalDiagnostics("US100-Scanner")
    logger.info("Diagnostic system initialized")
    
    # Validate configuration
    validator = ConfigValidator()
    warnings = validator.validate_config(config)
    if warnings:
        for warning in warnings:
            logger.warning(f"Config: {warning}")
    
    # Initialize components
    market_client = YFinanceClient(
        symbol=config['symbol'],
        timeframes=config['timeframes'],
        buffer_size=500
    )
    
    indicator_calc = IndicatorCalculator()
    
    # Initialize signal detector with diagnostics
    signal_detector = SignalDetector(
        volume_spike_threshold=config['signal_rules']['volume_spike_threshold'],
        rsi_min=config['signal_rules']['rsi_min'],
        rsi_max=config['signal_rules']['rsi_max'],
        stop_loss_atr_multiplier=config['signal_rules']['stop_loss_atr_multiplier'],
        take_profit_atr_multiplier=config['signal_rules']['take_profit_atr_multiplier'],
        duplicate_time_window_minutes=config['signal_rules']['duplicate_time_window_minutes'],
        duplicate_price_threshold_percent=config['signal_rules']['duplicate_price_threshold_percent'],
        diagnostics=diagnostics
    )
    
    # Set config for detection strategies
    signal_detector.config = {
        'signal_rules': config.get('signal_rules', {}),
        'asset_specific': config.get('asset_specific', {})
    }
    
    # Configure H4 HVG if enabled
    if config.get('h4_hvg', {}).get('enabled', False):
        signal_detector.configure_h4_hvg(config['h4_hvg'], config['symbol'])
        logger.info("H4 HVG detection enabled for US100/NASDAQ")
    
    # Initialize quality filter with diagnostics
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
    
    # Initialize alerter
    alerter = None
    if config['telegram']['enabled']:
        bot_token = config['telegram'].get('bot_token') or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = config['telegram'].get('chat_id') or os.getenv('TELEGRAM_CHAT_ID')
        
        if bot_token and chat_id:
            alerter = TelegramAlerter(bot_token, chat_id)
            logger.info("Telegram alerter initialized")
        else:
            logger.warning("Telegram credentials not found")
    
    # Initialize bypass mode
    bypass_mode = BypassMode(config, alerter)
    
    # Initialize trade tracker
    trade_tracker = TradeTracker(alerter=alerter)
    
    # Initialize Excel reporter
    excel_reporter = None
    if config.get('excel_reporting', {}).get('enabled', False):
        try:
            smtp_config = config['excel_reporting'].get('smtp', {})
            if smtp_config.get('password') and smtp_config['password'] != 'DISABLED':
                excel_reporter = ExcelReporter(
                    excel_file_path=config['excel_reporting'].get('excel_file_path', 'logs/us100_scans.xlsx'),
                    smtp_config=smtp_config,
                    report_interval_seconds=config['excel_reporting'].get('report_interval_seconds', 3600),
                    initial_report_delay_seconds=config['excel_reporting'].get('initial_report_delay_seconds', 300),
                    scanner_name="US100 Scanner"
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
        candles = indicator_calc.calculate_all_indicators(
            candles,
            ema_periods=[9, 21, 50, 100, 200],
            atr_period=14,
            rsi_period=14,
            volume_ma_period=20
        )
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
    # Send startup notification
    if alerter:
        try:
            df = candle_data[config['timeframes'][0]]
            current_price = df.iloc[-1]['close'] if not df.empty else 0
            
            startup_msg = (
                f"🚀 <b>US100/NASDAQ Scanner Started</b>\n\n"
                f"💰 Current Price: ${current_price:,.2f}\n"
                f"⏰ Timeframes: {', '.join(config['timeframes'])}\n"
                f"🎯 Strategies: H4-HVG, Momentum Shift, Trend Alignment, EMA Cloud, Mean Reversion\n"
                f"📊 Symbol: {config['symbol']}\n\n"
                f"🔍 Scanning for opportunities..."
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
            # Check bypass mode auto-disable
            bypass_mode.check_auto_disable()
            
            # Update data for each timeframe
            for timeframe in config['timeframes']:
                try:
                    # Fetch latest candles
                    candles, is_fresh = market_client.get_latest_candles(timeframe, count=500, validate_freshness=False)
                    
                    # Calculate indicators
                    candles = indicator_calc.calculate_all_indicators(
                        candles,
                        ema_periods=[9, 21, 50, 100, 200],
                        atr_period=14,
                        rsi_period=14,
                        volume_ma_period=20
                    )
                    
                    candle_data[timeframe] = candles
                    
                    # Detect signals
                    detected_signal = signal_detector.detect_signals(candles, timeframe, "US100")
                    
                    # Log scan result to Excel
                    if excel_reporter and not candles.empty:
                        last_row = candles.iloc[-1]
                        scanner_name = 'US100'
                        if detected_signal and getattr(detected_signal, 'strategy', '') == 'H4 HVG':
                            scanner_name = 'US100-H4HVG'
                        
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
                                'rsi': last_row.get('rsi', None),
                                'atr': last_row.get('atr', None),
                                'adx': last_row.get('adx', None)
                            },
                            'signal_detected': detected_signal is not None,
                            'signal_type': detected_signal.signal_type if detected_signal else None,
                            'signal_details': {
                                'entry_price': detected_signal.entry_price,
                                'stop_loss': detected_signal.stop_loss,
                                'take_profit': detected_signal.take_profit,
                                'risk_reward': detected_signal.risk_reward,
                                'strategy': detected_signal.strategy,
                                'confidence': detected_signal.confidence
                            } if detected_signal else {}
                        }
                        excel_reporter.log_scan_result(scan_data)
                    
                    if detected_signal:
                        logger.info(f"🚨 {detected_signal.signal_type} SIGNAL on {timeframe}!")
                        logger.info(f"Strategy: {detected_signal.strategy}")
                        logger.info(f"Entry: ${detected_signal.entry_price:.2f}, SL: ${detected_signal.stop_loss:.2f}, TP: ${detected_signal.take_profit:.2f}")
                        logger.info(f"Confidence: {detected_signal.confidence}/5, R:R = {detected_signal.risk_reward:.2f}")
                        
                        # Apply quality filter (unless bypass mode)
                        if bypass_mode.should_bypass_filters():
                            logger.warning("⚠️ BYPASS MODE - Skipping quality filter")
                            signal_to_send = detected_signal
                        else:
                            filter_result = quality_filter.evaluate_signal(detected_signal, candles)
                            
                            if filter_result.passed:
                                logger.info(f"✓ Signal passed quality filter")
                                signal_to_send = detected_signal
                            else:
                                logger.info(f"✗ Signal rejected by quality filter: {filter_result.rejection_reason}")
                                signal_to_send = None
                        
                        # Send alert if signal passed
                        if signal_to_send and alerter:
                            prefix = bypass_mode.format_signal_prefix()
                            alerter.send_signal_alert(signal_to_send)
                            quality_filter.add_signal_to_history(signal_to_send)
                            
                            # Track trade
                            trade_tracker.add_trade(signal_to_send)
                
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
                        'volume_ratio': last_candle['volume'] / last_candle.get('volume_ma', 1) if last_candle.get('volume_ma', 0) > 0 else 0
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
                        
                        # Generate diagnostic report
                        report = diagnostics.generate_report()
                        
                        heartbeat_msg = (
                            f"💙 <b>US100 Scanner Heartbeat</b>\n\n"
                            f"⏰ Time: {datetime.now().strftime('%H:%M:%S UTC')}\n"
                            f"💰 Price: ${last_candle['close']:,.2f}\n"
                            f"📊 RSI: {last_candle.get('rsi', 0):.1f}\n"
                            f"📈 ADX: {last_candle.get('adx', 0):.1f}\n"
                            f"🔍 Status: Actively scanning...\n\n"
                            f"{report.to_telegram_message()}"
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
        
        # Generate final diagnostic report
        logger.info("\n" + diagnostics.generate_report_text())
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
