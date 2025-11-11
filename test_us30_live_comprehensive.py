"""
Comprehensive US30 Live Data Test
Test US30 signal generation with real market data and detailed diagnostics
"""
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG to see everything
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.market_data_client import MarketDataClient
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector


def test_us30_signal_generation():
    """Test US30 with live data and detailed diagnostics"""
    logger.info("=" * 80)
    logger.info("US30 LIVE DATA COMPREHENSIVE TEST")
    logger.info("=" * 80)
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        market_client = MarketDataClient(
            exchange_name='kraken',
            symbol='US30/USD',  # Try US30
            timeframes=['5m'],
            buffer_size=200
        )
        
        indicator_calc = IndicatorCalculator()
        
        signal_detector = SignalDetector(
            volume_spike_threshold=0.8,  # Lower for US30
            rsi_min=30,
            rsi_max=70,
            stop_loss_atr_multiplier=1.5,
            take_profit_atr_multiplier=2.0
        )
        
        # Configure with US30-specific settings
        signal_detector.config = {
            'signal_rules': {
                'volume_momentum_shift': 0.8,  # US30 specific
                'volume_trend_alignment': 0.8,
                'volume_ema_cloud_breakout': 1.5,
                'volume_mean_reversion': 1.5,
                'rsi_momentum_threshold': 3.0,
                'adx_min_momentum_shift': 18,
                'adx_min_trend_alignment': 19,
                'momentum_shift_sl_multiplier': 1.2,
                'momentum_shift_tp_multiplier': 2.0,
            },
            'asset_specific': {
                'US30': {
                    'adx_threshold': 22,
                    'volume_thresholds': {
                        'momentum_shift': 0.8,
                        'trend_alignment': 0.8,
                        'breakout': 1.5,
                        'mean_reversion': 1.5
                    },
                    'rsi_momentum_threshold': 3.0
                }
            }
        }
        
        logger.info("✓ Components initialized with US30-specific config")
        
        # Connect and fetch data
        logger.info("Connecting to exchange...")
        if not market_client.connect():
            logger.error("Failed to connect")
            return False
        
        logger.info("✓ Connected")
        logger.info("Fetching US30 data...")
        
        data = market_client.get_latest_candles('5m', count=200)
        
        if data.empty:
            logger.error("No data received")
            return False
        
        logger.info(f"✓ Received {len(data)} candles")
        logger.info(f"  Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
        logger.info(f"  Latest: ${data.iloc[-1]['close']:.2f} @ {data.iloc[-1]['timestamp']}")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        data_with_indicators = indicator_calc.calculate_all_indicators(data)
        
        if data_with_indicators.empty:
            logger.error("Indicator calculation failed")
            return False
        
        logger.info(f"✓ Indicators calculated ({len(data_with_indicators)} rows)")
        
        # Show last candle indicators
        last = data_with_indicators.iloc[-1]
        logger.info("=" * 80)
        logger.info("LATEST CANDLE INDICATORS:")
        logger.info("=" * 80)
        logger.info(f"  Price: ${last['close']:.2f}")
        logger.info(f"  RSI: {last.get('rsi', 'N/A')}")
        logger.info(f"  ADX: {last.get('adx', 'N/A')}")
        logger.info(f"  EMA9: ${last.get('ema_9', 0):.2f}")
        logger.info(f"  EMA21: ${last.get('ema_21', 0):.2f}")
        logger.info(f"  EMA50: ${last.get('ema_50', 0):.2f}")
        logger.info(f"  Volume: {last.get('volume', 0):.0f}")
        logger.info(f"  Volume MA: {last.get('volume_ma', 0):.0f}")
        if 'volume_ma' in last.index and last['volume_ma'] > 0:
            logger.info(f"  Volume Ratio: {last['volume']/last['volume_ma']:.2f}x")
        logger.info(f"  ATR: ${last.get('atr', 0):.2f}")
        logger.info(f"  VWAP: ${last.get('vwap', 0):.2f}")
        
        # Check RSI history for momentum
        if len(data_with_indicators) >= 3:
            logger.info("")
            logger.info("RSI MOMENTUM CHECK:")
            rsi_current = data_with_indicators.iloc[-1].get('rsi', 0)
            rsi_prev = data_with_indicators.iloc[-2].get('rsi', 0)
            rsi_prev2 = data_with_indicators.iloc[-3].get('rsi', 0)
            rsi_change = rsi_current - rsi_prev2
            logger.info(f"  RSI: {rsi_prev2:.1f} -> {rsi_prev:.1f} -> {rsi_current:.1f}")
            logger.info(f"  Change: {rsi_change:+.1f} (need ±3.0 for momentum shift)")
            
            if rsi_current > rsi_prev > rsi_prev2:
                logger.info(f"  ✓ Bullish RSI momentum detected")
            elif rsi_current < rsi_prev < rsi_prev2:
                logger.info(f"  ✓ Bearish RSI momentum detected")
            else:
                logger.info(f"  ✗ No clear RSI momentum")
        
        # Test each strategy
        logger.info("")
        logger.info("=" * 80)
        logger.info("TESTING ALL STRATEGIES:")
        logger.info("=" * 80)
        
        strategies = [
            ('Momentum Shift', signal_detector._detect_momentum_shift),
            ('Trend Alignment', signal_detector._detect_trend_alignment),
            ('EMA Cloud Breakout', signal_detector._detect_ema_cloud_breakout),
            ('Mean Reversion', signal_detector._detect_mean_reversion),
        ]
        
        signals_found = []
        
        for strategy_name, strategy_func in strategies:
            logger.info(f"\n--- Testing {strategy_name} ---")
            try:
                signal = strategy_func(data_with_indicators, '5m', 'US30')
                if signal:
                    logger.info(f"✅ {strategy_name} GENERATED SIGNAL!")
                    logger.info(f"   Type: {signal.signal_type}")
                    logger.info(f"   Entry: ${signal.entry_price:.2f}")
                    logger.info(f"   Stop: ${signal.stop_loss:.2f}")
                    logger.info(f"   Target: ${signal.take_profit:.2f}")
                    logger.info(f"   R:R: {signal.risk_reward:.2f}")
                    logger.info(f"   Reasoning: {signal.reasoning}")
                    signals_found.append((strategy_name, signal))
                else:
                    logger.info(f"❌ {strategy_name} - No signal")
            except Exception as e:
                logger.error(f"❌ {strategy_name} - Error: {e}", exc_info=True)
        
        # Test main detect_signals method
        logger.info("")
        logger.info("=" * 80)
        logger.info("TESTING MAIN DETECT_SIGNALS METHOD:")
        logger.info("=" * 80)
        
        main_signal = signal_detector.detect_signals(data_with_indicators, '5m', 'US30')
        
        if main_signal:
            logger.info(f"✅ MAIN METHOD GENERATED SIGNAL!")
            logger.info(f"   Strategy: {main_signal.strategy}")
            logger.info(f"   Type: {main_signal.signal_type}")
            logger.info(f"   Entry: ${main_signal.entry_price:.2f}")
        else:
            logger.info(f"❌ MAIN METHOD - No signal")
        
        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("SUMMARY:")
        logger.info("=" * 80)
        logger.info(f"Total signals found: {len(signals_found)}")
        if signals_found:
            for strategy_name, signal in signals_found:
                logger.info(f"  - {strategy_name}: {signal.signal_type}")
            return True
        else:
            logger.warning("⚠️  NO SIGNALS GENERATED")
            logger.warning("This could mean:")
            logger.warning("  1. Market conditions don't meet any strategy criteria")
            logger.warning("  2. Thresholds are too strict for US30")
            logger.warning("  3. Data quality issues")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_us30_signal_generation()
    logger.info("")
    logger.info("=" * 80)
    if success:
        logger.info("✅ TEST PASSED - US30 signals are being generated")
    else:
        logger.info("⚠️  TEST COMPLETED - Check diagnostics above")
    logger.info("=" * 80)
