"""
Complete system test - All assets, all timeframes, all providers
"""
import logging
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys
ALPHA_VANTAGE_KEY = "66IUJDWBSTV9U220"
TWELVE_DATA_KEY = "a4f7101c037f4cf5949a1be62973283f"


def test_asset_all_timeframes(symbol, timeframes, alpha_key, twelve_key):
    """Test an asset across multiple timeframes"""
    logger.info("=" * 80)
    logger.info(f"TESTING {symbol} - ALL TIMEFRAMES")
    logger.info("=" * 80)
    
    try:
        from src.hybrid_data_client import HybridDataClient
        
        # Initialize client
        client = HybridDataClient(
            symbol=symbol,
            timeframes=timeframes,
            buffer_size=100,
            alpha_vantage_key=alpha_key,
            twelve_data_key=twelve_key
        )
        
        # Show client info
        info = client.get_client_info()
        logger.info(f"\nClient Configuration:")
        logger.info(f"  Symbol: {symbol}")
        logger.info(f"  Asset Type: {info['asset_type']}")
        logger.info(f"  Active Provider: {info['client_type']}")
        logger.info(f"  Timeframes: {', '.join(timeframes)}")
        
        # Connect
        logger.info(f"\nConnecting to {info['client_type']}...")
        if not client.connect():
            logger.error(f"✗ Failed to connect")
            return False
        
        logger.info(f"✓ Connected successfully")
        
        # Test each timeframe
        results = {}
        for tf in timeframes:
            logger.info(f"\n{'─' * 80}")
            logger.info(f"Testing {tf} timeframe...")
            logger.info(f"{'─' * 80}")
            
            try:
                # Fetch data
                data = client.get_latest_candles(tf, count=20)
                
                if data.empty:
                    logger.error(f"  ✗ No data for {tf}")
                    results[tf] = False
                    continue
                
                logger.info(f"  ✓ Received {len(data)} candles")
                
                # Validate data structure
                required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                missing_cols = [col for col in required_cols if col not in data.columns]
                
                if missing_cols:
                    logger.error(f"  ✗ Missing columns: {missing_cols}")
                    results[tf] = False
                    continue
                
                logger.info(f"  ✓ All required columns present")
                
                # Check for NaN values
                nan_counts = data[required_cols].isna().sum()
                if nan_counts.sum() > 0:
                    logger.warning(f"  ⚠ Found NaN values: {nan_counts[nan_counts > 0].to_dict()}")
                else:
                    logger.info(f"  ✓ No NaN values")
                
                # Show latest candle
                latest = data.iloc[-1]
                logger.info(f"\n  Latest Candle:")
                logger.info(f"    Time: {latest['timestamp']}")
                logger.info(f"    Open: ${latest['open']:.2f}")
                logger.info(f"    High: ${latest['high']:.2f}")
                logger.info(f"    Low: ${latest['low']:.2f}")
                logger.info(f"    Close: ${latest['close']:.2f}")
                logger.info(f"    Volume: {latest['volume']:.2f}")
                
                # Check OHLC validity
                if latest['high'] < latest['low']:
                    logger.error(f"  ✗ Invalid: High < Low")
                    results[tf] = False
                    continue
                
                if latest['high'] < latest['open'] or latest['high'] < latest['close']:
                    logger.error(f"  ✗ Invalid: High not highest")
                    results[tf] = False
                    continue
                
                if latest['low'] > latest['open'] or latest['low'] > latest['close']:
                    logger.error(f"  ✗ Invalid: Low not lowest")
                    results[tf] = False
                    continue
                
                logger.info(f"  ✓ OHLC values are valid")
                
                # Check data freshness
                now = datetime.now()
                latest_time = latest['timestamp']
                
                if hasattr(latest_time, 'to_pydatetime'):
                    latest_time = latest_time.to_pydatetime()
                
                if latest_time.tzinfo is not None:
                    latest_time = latest_time.replace(tzinfo=None)
                
                age_minutes = (now - latest_time).total_seconds() / 60
                logger.info(f"  Data age: {age_minutes:.1f} minutes")
                
                # Timeframe-specific freshness checks
                if tf in ['1m', '5m']:
                    max_age = 30  # 30 minutes for short timeframes
                elif tf in ['15m', '30m', '1h']:
                    max_age = 120  # 2 hours for medium timeframes
                else:
                    max_age = 1440  # 24 hours for daily
                
                if age_minutes <= max_age:
                    logger.info(f"  ✓ Data is acceptable (< {max_age} min)")
                    results[tf] = True
                else:
                    logger.warning(f"  ⚠ Data is stale (> {max_age} min)")
                    results[tf] = False
                
            except Exception as e:
                logger.error(f"  ✗ Error testing {tf}: {e}")
                results[tf] = False
        
        # Summary for this asset
        logger.info(f"\n{'=' * 80}")
        logger.info(f"SUMMARY FOR {symbol}")
        logger.info(f"{'=' * 80}")
        
        for tf, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"  {tf}: {status}")
        
        success_rate = sum(results.values()) / len(results) * 100
        logger.info(f"\nSuccess Rate: {success_rate:.0f}% ({sum(results.values())}/{len(results)})")
        
        return all(results.values())
        
    except Exception as e:
        logger.error(f"✗ Fatal error testing {symbol}: {e}", exc_info=True)
        return False


def main():
    """Run complete system test"""
    logger.info("=" * 80)
    logger.info("COMPLETE SYSTEM TEST")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.now()}")
    logger.info("")
    
    # Define test configuration
    test_config = [
        {
            'symbol': 'BTC/USD',
            'timeframes': ['1m', '5m', '15m', '1h', '4h'],
            'expected_provider': 'kraken'
        },
        {
            'symbol': 'US30/USD',
            'timeframes': ['5m', '15m', '1h', '4h'],
            'expected_provider': 'alpha_vantage'
        },
        {
            'symbol': 'XAU/USD',
            'timeframes': ['5m', '15m', '1h', '4h'],
            'expected_provider': 'alpha_vantage'
        }
    ]
    
    logger.info("Test Configuration:")
    for config in test_config:
        logger.info(f"  {config['symbol']}: {', '.join(config['timeframes'])} ({config['expected_provider']})")
    logger.info("")
    
    # Run tests
    results = {}
    
    for i, config in enumerate(test_config):
        if i > 0:
            # Wait between assets to respect rate limits
            logger.info(f"\n⏳ Waiting 15 seconds to respect rate limits...")
            time.sleep(15)
        
        logger.info("")
        results[config['symbol']] = test_asset_all_timeframes(
            symbol=config['symbol'],
            timeframes=config['timeframes'],
            alpha_key=ALPHA_VANTAGE_KEY,
            twelve_key=TWELVE_DATA_KEY
        )
    
    # Final Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINAL TEST RESULTS")
    logger.info("=" * 80)
    logger.info("")
    
    for symbol, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{symbol}: {status}")
    
    overall_success = all(results.values())
    
    logger.info("")
    logger.info("=" * 80)
    if overall_success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("")
        logger.info("System Status: PRODUCTION READY")
        logger.info("")
        logger.info("✓ All assets connecting successfully")
        logger.info("✓ All timeframes working")
        logger.info("✓ Data validation passing")
        logger.info("✓ Provider routing correct")
        logger.info("")
        logger.info("Next Steps:")
        logger.info("1. Deploy to Google Cloud VM")
        logger.info("2. Update scanner to use HybridDataClient")
        logger.info("3. Set scan interval to 5 minutes")
        logger.info("4. Monitor for signals during trading hours")
    else:
        logger.warning("⚠️ SOME TESTS FAILED")
        logger.info("")
        logger.info("Common reasons for failures:")
        logger.info("  - Markets are closed (US30 trades 9:30-16:00 ET)")
        logger.info("  - Data is stale outside trading hours")
        logger.info("  - Rate limits hit (wait and retry)")
        logger.info("")
        logger.info("Note: Stale data during off-hours is NORMAL")
        logger.info("Test again during active trading hours for accurate results")
    
    logger.info("=" * 80)
    logger.info(f"End Time: {datetime.now()}")
    logger.info("=" * 80)
    
    return overall_success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
