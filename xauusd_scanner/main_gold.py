"""
XAU/USD Gold Scalping Scanner
Session-aware Gold trading with news calendar and spread monitoring
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.yfinance_client import YFinanceClient
from src.indicator_calculator import IndicatorCalculator
from src.alerter import TelegramAlerter
from src.trade_tracker import TradeTracker
from src.excel_reporter import ExcelReporter

from xauusd_scanner.session_manager import SessionManager, TradingSession
from xauusd_scanner.news_calendar import NewsCalendar
from xauusd_scanner.spread_monitor import SpreadMonitor
from xauusd_scanner.key_level_tracker import KeyLevelTracker
from xauusd_scanner.strategy_selector import StrategySelector
from xauusd_scanner.gold_signal_detector import GoldSignalDetector


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


def load_config(config_path: str = "xauusd_scanner/config_gold.json") -> dict:
    """Load configuration."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    """Main Gold scanner loop."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(
        config['logging']['file'],
        config['logging']['level']
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("XAU/USD Gold Scalping Scanner Starting")
    logger.info("=" * 60)
    
    # Initialize core components
    logger.info("Initializing components...")
    
    # Use YFinance client for Gold data
    market_client = YFinanceClient(
        symbol='GC=F',  # Gold Futures
        timeframes=config['exchange']['timeframes'],
        buffer_size=200
    )
    
    indicator_calc = IndicatorCalculator()
    
    # Initialize Gold-specific components
    session_manager = SessionManager()
    news_calendar = NewsCalendar(config.get('news_events_file', 'xauusd_scanner/news_events.json'))
    spread_monitor = SpreadMonitor(
        acceptable_spread_pips=config['spread_monitoring']['acceptable_pips'],
        pause_spread_pips=config['spread_monitoring']['pause_pips']
    )
    key_level_tracker = KeyLevelTracker()
    strategy_selector = StrategySelector(session_manager)
    
    signal_detector = GoldSignalDetector(
        session_manager=session_manager,
        key_level_tracker=key_level_tracker,
        strategy_selector=strategy_selector
    )
    
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
                    excel_file_path=config['excel_reporting'].get('excel_file_path', 'logs/xauusd_scalp_scans.xlsx'),
                    smtp_config=smtp_config,
                    report_interval_seconds=config['excel_reporting'].get('report_interval_seconds', 3600),
                    initial_report_delay_seconds=config['excel_reporting'].get('initial_report_delay_seconds', 300),
                    scanner_name="XAUUSD Scalp Scanner"
                )
                excel_reporter.start()
                logger.info("Excel reporting enabled")
            else:
                logger.warning("Excel reporting disabled: SMTP password not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Excel reporter: {e}")
    
    logger.info("All components initialized successfully")
    
    # Connect to data source
    logger.info("Connecting to Yahoo Finance for Gold data...")
    if not market_client.connect():
        logger.error("Failed to connect to Yahoo Finance")
        sys.exit(1)
    logger.info("Successfully connected to Yahoo Finance")
    
    # Fetch initial data
    logger.info("Fetching initial candlestick data...")
    candle_data = {}
    for timeframe in config['exchange']['timeframes']:
        candles = market_client.get_latest_candles(timeframe, count=500)
        
        # Calculate indicators
        candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)
        candles['ema_21'] = indicator_calc.calculate_ema(candles, 21)
        candles['ema_50'] = indicator_calc.calculate_ema(candles, 50)
        candles['vwap'] = indicator_calc.calculate_vwap(candles)
        candles['atr'] = indicator_calc.calculate_atr(candles, 14)
        candles['rsi'] = indicator_calc.calculate_rsi(candles, 14)
        candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, 20)
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
    # Send startup notification
    if alerter:
        session_info = session_manager.get_session_info()
        alerter.send_message(
            f"🟢 <b>XAU/USD Gold Scanner Started</b>\n\n"
            f"Session: {session_info['session']}\n"
            f"Strategy: {session_info['strategy_focus']}\n"
            f"Monitoring: {', '.join(config['exchange']['timeframes'])}\n\n"
            f"Ready to scan for Gold signals!"
        )
    
    logger.info("Scanner is now running. Press Ctrl+C to stop.")
    
    # Track state
    last_session = None
    last_news_pause = False
    last_spread_pause = False
    
    try:
        while True:
            # Get current session
            current_session = session_manager.get_current_session()
            
            # Check for session change
            if current_session != last_session:
                session_info = session_manager.get_session_info()
                logger.info(f"📍 Session: {session_info['session']} - {session_info['recommendation']}")
                
                if alerter and last_session is not None:
                    alerter.send_message(
                        f"🔄 <b>Session Change</b>\n\n"
                        f"Now: {session_info['session']}\n"
                        f"Focus: {session_info['strategy_focus']}\n"
                        f"Recommendation: {session_info['recommendation']}"
                    )
                
                last_session = current_session
                
                # Finalize Asian range if transitioning to London
                if current_session == TradingSession.LONDON:
                    asian_range = session_manager.finalize_asian_range()
                    if asian_range.get('finalized'):
                        logger.info(f"Asian range finalized: {asian_range['range_pips']:.1f} pips")
            
            # Check news calendar
            should_pause_news, news_reason = news_calendar.should_pause_trading()
            
            if should_pause_news != last_news_pause:
                if should_pause_news:
                    logger.warning(f"📰 Trading paused: {news_reason}")
                    if alerter:
                        alerter.send_message(f"⏸️ <b>Trading Paused</b>\n\n{news_reason}")
                else:
                    logger.info("✅ Trading resumed after news")
                    if alerter:
                        alerter.send_message("▶️ <b>Trading Resumed</b>\n\nNews event passed, back to normal trading.")
                
                last_news_pause = should_pause_news
            
            # Skip trading if paused for news
            if should_pause_news:
                time.sleep(30)
                continue
            
            # Update data for each timeframe
            for timeframe in config['exchange']['timeframes']:
                try:
                    # Fetch latest candles
                    candles = market_client.get_latest_candles(timeframe, count=500)
                    
                    # Calculate indicators
                    candles['ema_9'] = indicator_calc.calculate_ema(candles, 9)
                    candles['ema_21'] = indicator_calc.calculate_ema(candles, 21)
                    candles['ema_50'] = indicator_calc.calculate_ema(candles, 50)
                    candles['vwap'] = indicator_calc.calculate_vwap(candles)
                    candles['atr'] = indicator_calc.calculate_atr(candles, 14)
                    candles['rsi'] = indicator_calc.calculate_rsi(candles, 14)
                    candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, 20)
                    
                    candle_data[timeframe] = candles
                    
                    # Update key levels
                    last_candle = candles.iloc[-1]
                    key_level_tracker.update_levels(
                        high=last_candle['high'],
                        low=last_candle['low'],
                        close=last_candle['close'],
                        timestamp=last_candle['timestamp']
                    )
                    
                    # Update Asian range if in Asian session
                    if current_session == TradingSession.ASIAN:
                        session_manager.update_asian_range(
                            high=last_candle['high'],
                            low=last_candle['low']
                        )
                    
                    # Update spread (simulate with bid/ask from close)
                    # In production, get real bid/ask from exchange
                    spread_pips = 0.5  # Typical Gold spread
                    bid = last_candle['close'] - (spread_pips / 10)
                    ask = last_candle['close'] + (spread_pips / 10)
                    spread_monitor.update_spread(bid, ask)
                    
                    # Check spread
                    should_pause_spread, spread_reason = spread_monitor.should_pause_trading()
                    
                    if should_pause_spread != last_spread_pause:
                        if should_pause_spread:
                            logger.warning(f"📊 Trading paused: {spread_reason}")
                            if alerter:
                                alerter.send_message(f"⏸️ <b>Spread Too Wide</b>\n\n{spread_reason}")
                        else:
                            logger.info("✅ Spread back to normal")
                        
                        last_spread_pause = should_pause_spread
                    
                    # Skip if spread too wide
                    if should_pause_spread:
                        continue
                    
                    # Detect signals
                    signal = signal_detector.detect_signals(candles, timeframe)
                    
                    # Log scan result to Excel
                    if excel_reporter and not candles.empty:
                        last_candle = candles.iloc[-1]
                        session_info = session_manager.get_session_info()
                        scan_data = {
                            'timestamp': datetime.now(),
                            'scanner': f"XAUUSD-Scalp-{session_info['session']}",
                            'symbol': config['exchange']['symbol'],
                            'timeframe': timeframe,
                            'price': last_candle['close'],
                            'volume': last_candle['volume'],
                            'indicators': {
                                'ema_9': last_candle.get('ema_9', None),
                                'ema_21': last_candle.get('ema_21', None),
                                'ema_50': last_candle.get('ema_50', None),
                                'rsi': last_candle.get('rsi', None),
                                'atr': last_candle.get('atr', None),
                                'volume_ma': last_candle.get('volume_ma', None),
                                'vwap': last_candle.get('vwap', None)
                            },
                            'signal_detected': signal is not None,
                            'signal_type': signal.signal_type if signal else None,
                            'signal_details': {
                                'entry_price': signal.entry_price,
                                'stop_loss': signal.stop_loss,
                                'take_profit': signal.take_profit,
                                'risk_reward': signal.risk_reward,
                                'strategy': getattr(signal, 'strategy', 'N/A')
                            } if signal else {}
                        }
                        excel_reporter.log_scan_result(scan_data)
                    
                    if signal:
                        # Add spread info
                        signal.spread_pips = spread_monitor.current_spread_pips
                        
                        logger.info(f"🚨 {signal.signal_type} SIGNAL on {timeframe}!")
                        logger.info(f"Strategy: {signal.strategy}")
                        logger.info(f"Entry: ${signal.entry_price:.2f}, SL: ${signal.stop_loss:.2f}, TP: ${signal.take_profit:.2f}")
                        logger.info(f"R:R = {signal.risk_reward:.2f}, Spread: {signal.spread_pips:.1f} pips")
                        
                        # Send alert
                        if alerter:
                            alerter.send_signal_alert(signal)
                        
                        # Track trade
                        trade_tracker.add_trade(signal)
                
                except Exception as e:
                    logger.error(f"Error processing {timeframe}: {e}")
            
            # Check for trade updates
            try:
                current_price = candle_data[config['exchange']['timeframes'][0]].iloc[-1]['close']
                trade_tracker.update_trades(current_price)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Determine polling interval based on session
            if current_session == TradingSession.ASIAN:
                # Slower during Asian (range-bound)
                interval = config.get('asian_polling_seconds', 30)
            else:
                # Faster during active sessions
                interval = config['scanner']['polling_interval_seconds']
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scanner stopped by user")
        logger.info("=" * 60)
        
        # Stop Excel reporter
        if excel_reporter:
            excel_reporter.stop()
        
        # Send shutdown notification
        if alerter:
            alerter.send_message("🔴 <b>XAU/USD Scanner Stopped</b>\n\nScanner has been shut down.")
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        
        if alerter:
            alerter.send_message(f"❌ <b>Scanner Error</b>\n\nFatal error occurred. Check logs.")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
