"""
US30 (Dow Jones) Scalping Scanner
High-frequency trading for NY session with liquidity sweep and trend pullback strategies
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

from us30_scanner.us30_scalp_detector import US30ScalpDetector


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


def load_config(config_path: str = "us30_scanner/config_us30_scalp.json") -> dict:
    """Load configuration."""
    with open(config_path, 'r') as f:
        return json.load(f)


def is_trading_hours(config: dict) -> bool:
    """Check if current time is within NY trading hours."""
    try:
        now = datetime.now(timezone.utc)
        current_time = now.strftime('%H:%M')
        
        start_time = config['trading_hours']['ny_open_start']
        end_time = config['trading_hours']['ny_open_end']
        
        return start_time <= current_time <= end_time
    except Exception:
        # If no trading hours specified, trade anytime
        return True


def main():
    """Main US30 scalping scanner loop."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(
        config['logging']['file'],
        config['logging']['level']
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("US30 Scalping Scanner Starting")
    logger.info("=" * 60)
    
    # Initialize components
    logger.info("Initializing components...")
    
    market_client = YFinanceClient(
        symbol=config['exchange']['symbol'],
        timeframes=config['exchange']['timeframes'],
        buffer_size=200
    )
    
    indicator_calc = IndicatorCalculator()
    
    signal_detector = US30ScalpDetector(config=config['signal_rules'])
    
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
        candles = market_client.get_latest_candles(timeframe, count=200)
        
        # Calculate indicators
        candles['ema_8'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_fast'])
        candles['ema_21'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_mid'])
        candles['ema_50'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_slow'])
        candles['vwap'] = indicator_calc.calculate_vwap(candles)
        candles['atr'] = indicator_calc.calculate_atr(candles, config['indicators']['atr_period'])
        candles['rsi'] = indicator_calc.calculate_rsi(candles, config['indicators']['rsi_period'])
        candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, config['indicators']['volume_ma_period'])
        
        # Calculate Stochastic
        stoch_k, stoch_d = indicator_calc.calculate_stochastic(
            candles,
            config['indicators']['stochastic_k'],
            config['indicators']['stochastic_d'],
            config['indicators']['stochastic_smooth']
        )
        candles['stoch_k'] = stoch_k
        candles['stoch_d'] = stoch_d
        
        candle_data[timeframe] = candles
        logger.info(f"Loaded {timeframe} data with indicators")
    
    # Send startup notification
    if alerter:
        current_price = candle_data[config['exchange']['timeframes'][0]].iloc[-1]['close']
        alerter.send_message(
            f"🟢 <b>US30 Scalping Scanner Started</b>\n\n"
            f"💰 Current Price: {current_price:,.2f}\n"
            f"⏰ Timeframes: {', '.join(config['exchange']['timeframes'])}\n"
            f"🎯 Strategy: Liquidity Sweep + Trend Pullback\n"
            f"📊 Best Hours: NY Open (14:30-17:00 GMT)\n\n"
            f"🔍 Scanning for scalping opportunities..."
        )
    
    logger.info("Scanner is now running. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Check if within trading hours
            if not is_trading_hours(config):
                logger.debug("Outside trading hours, waiting...")
                time.sleep(300)  # Check every 5 minutes
                continue
            
            # Update data for each timeframe
            for timeframe in config['exchange']['timeframes']:
                try:
                    # Fetch latest candles
                    candles = market_client.get_latest_candles(timeframe, count=200)
                    
                    # Calculate indicators
                    candles['ema_8'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_fast'])
                    candles['ema_21'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_mid'])
                    candles['ema_50'] = indicator_calc.calculate_ema(candles, config['indicators']['ema_slow'])
                    candles['vwap'] = indicator_calc.calculate_vwap(candles)
                    candles['atr'] = indicator_calc.calculate_atr(candles, config['indicators']['atr_period'])
                    candles['rsi'] = indicator_calc.calculate_rsi(candles, config['indicators']['rsi_period'])
                    candles['volume_ma'] = indicator_calc.calculate_volume_ma(candles, config['indicators']['volume_ma_period'])
                    
                    # Calculate Stochastic
                    stoch_k, stoch_d = indicator_calc.calculate_stochastic(
                        candles,
                        config['indicators']['stochastic_k'],
                        config['indicators']['stochastic_d'],
                        config['indicators']['stochastic_smooth']
                    )
                    candles['stoch_k'] = stoch_k
                    candles['stoch_d'] = stoch_d
                    
                    candle_data[timeframe] = candles
                    
                    # Detect signals
                    signal = signal_detector.detect_signals(candles, timeframe)
                    
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
                
                except Exception as e:
                    logger.error(f"Error processing {timeframe}: {e}")
            
            # Check for trade updates
            try:
                current_price = candle_data[config['exchange']['timeframes'][0]].iloc[-1]['close']
                updates = trade_tracker.check_for_updates(current_price)
                
                for update in updates:
                    logger.info(f"📊 Trade Update: {update['message']}")
                    if alerter:
                        alerter.send_trade_update(update)
            
            except Exception as e:
                logger.error(f"Error checking trade updates: {e}")
            
            # Sleep
            time.sleep(config['polling_interval_seconds'])
    
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Scanner stopped by user")
        logger.info("=" * 60)
        
        # Send shutdown notification
        if alerter:
            alerter.send_message("🔴 <b>US30 Scalping Scanner Stopped</b>\n\nScanner has been shut down.")
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        
        if alerter:
            alerter.send_message(f"❌ <b>Scanner Error</b>\n\nFatal error occurred. Check logs.")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
