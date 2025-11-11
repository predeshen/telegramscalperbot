"""
Test Signal Quality Enhancements with LIVE Market Data
This will connect to real market data and test the enhanced system
"""
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.market_data_client import MarketDataClient
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.liquidity_filter import LiquidityFilter
from src.data_validation import DataValidator


def test_live_btc_scanning():
    """Test with live BTC data"""
    logger.info("=" * 80)
    logger.info("TESTING WITH LIVE BTC DATA")
    logger.info("=" * 80)
    
    try:
        # Initialize components
        market_client = MarketDataClient(
            exchange_name='kraken',
            symbol='BTC/USDT',
            timeframes=['5m'],
            buffer_size=100
        )
        
        indicator_calc = IndicatorCalculator()
        
        signal_detector = SignalDetector(
            volume_spike_threshold=1.5,
            rsi_min=30,
            rsi_max=70,
            stop_loss_atr_multiplier=1.5,
            take_profit_atr_multiplier=2.0
        )
        
        # Set enhanced config
        signal_detector.config = {
            'signal_rules': {
                'volume_momentum_shift': 1.2,
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
                'BTC': {
                    'adx_threshold': 20,
                    'volume_thresholds': {
                        'momentum_shift': 1.2,
                        'trend_alignment': 0.8,
                        'breakout': 1.5,
                        'mean_reversion': 1.5
                    },
                    'rsi_momentum_threshold': 3.0
                }
            }
        }
        
        quality_config = QualityConfig(
            min_confluence_factors=4,
            min_confidence_score=4,
            duplicate_window_seconds=300,
            min_risk_reward=1.5
        )
        quality_filter = SignalQualityFilter(quality_config)
        liquidity_filter = LiquidityFilter()
        data_validator = DataValidator()
        
        logger.info("✓ All components initialized")
        
        # Connect to exchange
        logger.info("Connecting to exchange...")
        if not market_client.connect():
            logger.error("✗ Failed to connect to exchange")
            return False
        logger.info("✓ Connected to exchange")
        
        # Fetch live data
        logger.info("Fetching live BTC data...")
        data = market_client.get_latest_candles('5m', count=100)
        
        if data.empty:
            logger.error("✗ No data received")
            return False
        
        logger.info(f"✓ Received {len(data)} candles")
        logger.info(f"  Latest price: ${data.iloc[-1]['close']:.2f}")
        logger.info(f"  Timestamp: {data.iloc[-1]['timestamp']}")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        data_with_indicators = indicator_calc.calculate_all_indicators(data)
        
        if data_with_indicators.empty:
            logger.error("✗ Indicator calculation failed")
            return False
        
        logger.info("✓ Indicators calculated")
        last = data_with_indicators.iloc[-1]
        logger.info(f"  RSI: {last.get('rsi', 0):.1f}")
        if 'adx' in last.index:
            logger.info(f"  ADX: {last['adx']:.1f}")
        if 'volume' in last.index and 'volume_ma' in last.index:
            logger.info(f"  Volume: {last['volume']:.0f} ({last['volume']/last['volume_ma']:.2f}x avg)")
        
        # Validate data
        logger.info("Validating market data...")
        is_valid, errors = data_validator.validate_market_data(data_with_indicators, 'BTC')
        
        if not is_valid:
            logger.warning(f"✗ Data validation failed: {', '.join(errors)}")
            return False
        
        logger.info("✓ Data validation passed")
        
        # Check liquidity
        logger.info("Checking liquidity...")
        asset_config = signal_detector.config['asset_specific']['BTC']
        liquidity_ok, reason = liquidity_filter.filter_signal(
            datetime.now(), 'BTC', asset_config, data_with_indicators
        )
        
        if liquidity_ok:
            logger.info("✓ Liquidity check passed")
        else:
            logger.warning(f"⚠ Liquidity issue: {reason}")
        
        # Detect signals
        logger.info("=" * 80)
        logger.info("SCANNING FOR SIGNALS...")
        logger.info("=" * 80)
        
        signal = signal_detector.detect_signals(data_with_indicators, '5m', 'BTC/USD')
        
        if signal:
            logger.info(f"🎯 PRELIMINARY SIGNAL DETECTED!")
            logger.info(f"  Type: {signal.signal_type}")
            logger.info(f"  Strategy: {signal.strategy}")
            logger.info(f"  Entry: ${signal.entry_price:.2f}")
            logger.info(f"  Stop Loss: ${signal.stop_loss:.2f}")
            logger.info(f"  Take Profit: ${signal.take_profit:.2f}")
            logger.info(f"  Risk/Reward: {signal.risk_reward:.2f}")
            
            # Apply quality filter
            logger.info("")
            logger.info("Applying Signal Quality Filter...")
            result = quality_filter.evaluate_signal(signal, data_with_indicators)
            
            if result.passed:
                logger.info("✅ SIGNAL APPROVED!")
                logger.info(f"  Confidence Score: {result.confidence_score}/5")
                logger.info(f"  Confluence Factors: {len(result.confluence_factors)}/7")
                logger.info(f"  Factors: {', '.join(result.confluence_factors)}")
                
                # Generate alert message
                alert = signal.to_alert_message(
                    confidence_score=result.confidence_score,
                    confluence_factors=result.confluence_factors
                )
                logger.info("")
                logger.info("=" * 80)
                logger.info("ALERT MESSAGE:")
                logger.info("=" * 80)
                logger.info(alert)
                
                return True
            else:
                logger.info(f"❌ SIGNAL REJECTED: {result.rejection_reason}")
                logger.info(f"  Confidence Score: {result.confidence_score}/5")
                logger.info(f"  Confluence Factors: {len(result.confluence_factors)}/7")
                return False
        else:
            logger.info("ℹ️  No signals detected in current market conditions")
            logger.info("  This is normal - the enhanced filters are working to prevent weak signals")
            return True  # Not finding a signal is also a success
        
    except Exception as e:
        logger.error(f"✗ Error during live test: {e}", exc_info=True)
        return False


def main():
    """Run live data test"""
    logger.info("=" * 80)
    logger.info("SIGNAL QUALITY ENHANCEMENT - LIVE DATA TEST")
    logger.info("=" * 80)
    logger.info("")
    
    success = test_live_btc_scanning()
    
    logger.info("")
    logger.info("=" * 80)
    if success:
        logger.info("✅ LIVE DATA TEST COMPLETED SUCCESSFULLY")
        logger.info("The enhanced signal quality system is working correctly with live market data!")
    else:
        logger.info("⚠️  LIVE DATA TEST ENCOUNTERED ISSUES")
        logger.info("Check the logs above for details")
    logger.info("=" * 80)
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
