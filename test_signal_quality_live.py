"""
Test Signal Quality Enhancements with Live Data
Quick test to verify all enhancements are working
"""
import logging
import json
from datetime import datetime
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import enhanced components
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.liquidity_filter import LiquidityFilter
from src.data_validation import DataValidator
from src.signal_detector import SignalDetector, Signal
from src.market_data_models import MarketData


def test_quality_filter():
    """Test Signal Quality Filter"""
    logger.info("=" * 60)
    logger.info("Testing Signal Quality Filter")
    logger.info("=" * 60)
    
    # Create quality filter with enhanced config
    config = QualityConfig(
        min_confluence_factors=4,
        min_confidence_score=4,
        duplicate_window_seconds=300,
        duplicate_price_tolerance_pct=0.5,
        significant_price_move_pct=1.0,
        min_risk_reward=1.5
    )
    quality_filter = SignalQualityFilter(config)
    
    # Create a test signal
    test_signal = Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="5m",
        entry_price=45000.0,
        stop_loss=44700.0,
        take_profit=45600.0,
        atr=150.0,
        risk_reward=2.0,
        market_bias="bullish",
        confidence=4,
        indicators={
            'rsi': 55.0,
            'adx': 25.0,
            'ema_50': 44800.0,
            'volume': 1000.0,
            'volume_ma': 800.0
        },
        symbol="BTC/USD",
        strategy="Momentum Shift"
    )
    
    # Test evaluation
    result = quality_filter.evaluate_signal(test_signal)
    
    logger.info(f"✓ Quality Filter Test:")
    logger.info(f"  Passed: {result.passed}")
    logger.info(f"  Confidence Score: {result.confidence_score}/5")
    logger.info(f"  Confluence Factors: {len(result.confluence_factors)}/7")
    if result.rejection_reason:
        logger.info(f"  Rejection Reason: {result.rejection_reason}")
    
    return result.passed


def test_liquidity_filter():
    """Test Liquidity Filter"""
    logger.info("=" * 60)
    logger.info("Testing Liquidity Filter")
    logger.info("=" * 60)
    
    liquidity_filter = LiquidityFilter()
    
    # Test with current time
    timestamp = datetime.now()
    asset_config = {
        'trading_hours': None  # BTC trades 24/7
    }
    
    allowed, reason = liquidity_filter.filter_signal(
        timestamp, 'BTC', asset_config
    )
    
    logger.info(f"✓ Liquidity Filter Test:")
    logger.info(f"  Allowed: {allowed}")
    if reason:
        logger.info(f"  Reason: {reason}")
    
    return allowed


def test_data_validator():
    """Test Data Validator"""
    logger.info("=" * 60)
    logger.info("Testing Data Validator")
    logger.info("=" * 60)
    
    validator = DataValidator()
    
    # Create test data
    test_data = pd.DataFrame({
        'timestamp': [datetime.now()],
        'open': [45000.0],
        'high': [45100.0],
        'low': [44900.0],
        'close': [45050.0],
        'volume': [1000.0],
        'rsi': [55.0],
        'adx': [25.0],
        'ema_9': [45020.0],
        'ema_21': [44980.0],
        'ema_50': [44900.0],
        'atr': [150.0],
        'vwap': [45000.0],
        'volume_ma': [800.0]
    })
    
    is_valid, errors = validator.validate_market_data(test_data, 'BTC')
    
    logger.info(f"✓ Data Validator Test:")
    logger.info(f"  Valid: {is_valid}")
    if errors:
        logger.info(f"  Errors: {', '.join(errors)}")
    
    return is_valid


def test_asset_specific_config():
    """Test Asset-Specific Configuration"""
    logger.info("=" * 60)
    logger.info("Testing Asset-Specific Configuration")
    logger.info("=" * 60)
    
    # Load config
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    
    # Check asset-specific configs
    if 'asset_specific' in config:
        logger.info("✓ Asset-specific configuration found:")
        for asset, asset_config in config['asset_specific'].items():
            logger.info(f"  {asset}:")
            logger.info(f"    ADX Threshold: {asset_config.get('adx_threshold')}")
            logger.info(f"    Min Confluence: {asset_config.get('min_confluence_factors')}")
            logger.info(f"    RSI Momentum: {asset_config.get('rsi_momentum_threshold')}")
        return True
    else:
        logger.warning("✗ No asset-specific configuration found")
        return False


def test_signal_alert_message():
    """Test Signal Alert Message Formatting"""
    logger.info("=" * 60)
    logger.info("Testing Signal Alert Message")
    logger.info("=" * 60)
    
    test_signal = Signal(
        timestamp=datetime.now(),
        signal_type="LONG",
        timeframe="5m",
        entry_price=45000.0,
        stop_loss=44700.0,
        take_profit=45600.0,
        atr=150.0,
        risk_reward=2.0,
        market_bias="bullish",
        confidence=4,
        indicators={
            'rsi': 55.0,
            'adx': 25.0,
            'volume': 1000.0,
            'volume_ma': 800.0
        },
        symbol="BTC/USD",
        strategy="Momentum Shift",
        reasoning="RSI turning up with ADX confirmation"
    )
    
    # Generate alert message
    alert_message = test_signal.to_alert_message(
        confidence_score=4,
        confluence_factors=['trend', 'momentum', 'volume', 'price_action']
    )
    
    logger.info("✓ Alert Message Generated:")
    logger.info(alert_message)
    
    return True


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("SIGNAL QUALITY ENHANCEMENT TESTS")
    logger.info("=" * 60)
    
    results = {
        'Quality Filter': test_quality_filter(),
        'Liquidity Filter': test_liquidity_filter(),
        'Data Validator': test_data_validator(),
        'Asset Config': test_asset_specific_config(),
        'Alert Message': test_signal_alert_message()
    }
    
    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("✓ ALL TESTS PASSED!")
    else:
        logger.warning("✗ SOME TESTS FAILED")
    logger.info("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
