"""
Test multi-provider hybrid client with Alpha Vantage, Twelve Data, and yfinance
"""
import logging
from datetime import datetime
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys
ALPHA_VANTAGE_KEY = "66IUJDWBSTV9U220"
TWELVE_DATA_KEY = os.getenv('TWELVE_DATA_KEY')  # Get from environment if available


def test_symbol_with_providers(symbol, alpha_key=None, twelve_key=None):
    """Test a symbol with multiple providers"""
    logger.info("=" * 80)
    logger.info(f"TESTING {symbol}")
    logger.info("=" * 80)
    
    try:
        from src.hybrid_data_client import HybridDataClient
        
        # Initialize with all available keys
        client = HybridDataClient(
            symbol=symbol,
            timeframes=['5m'],
            buffer_size=100,
            alpha_vantage_key=alpha_key,
            twelve_data_key=twelve_key
        )
        
        # Show client info
        info = client.get_client_info()
        logger.info(f"\nClient Info:")
        logger.info(f"  Asset Type: {info['asset_type']}")
        logger.info(f"  Active Provider: {info['client_type']}")
        logger.info(f"  Providers Tried: {', '.join(info['providers_tried'])}")
        logger.info(f"  Has Alpha Vantage: {info['has_alpha_vantage']}")
        logger.info(f"  Has Twelve Data: {info['has_twelve_data']}")
        
        # Connect
        logger.info(f"\nConnecting...")
        if not client.connect():
            logger.error("✗ Failed to connect")
            return False
        
        logger.info(f"✓ Connected with {info['client_type']}")
        
        # Fetch data
        logger.info(f"\nFetching 5m candles...")
        data = client.get_latest_candles('5m', count=10)
        
        if data.empty:
            logger.error("✗ No data received")
            return False
        
        logger.info(f"✓ Received {len(data)} candles")
        
        # Show latest
        latest = data.iloc[-1]
        logger.info(f"\nLatest Candle:")
        logger.info(f"  Timestamp: {latest['timestamp']}")
        logger.info(f"  Close: ${latest['close']:.2f}")
        logger.info(f"  Volume: {latest['volume']:.2f}")
        
        # Check freshness
        now = datetime.now()
        latest_time = latest['timestamp']
        
        if hasattr(latest_time, 'to_pydatetime'):
            latest_time = latest_time.to_pydatetime()
        
        if latest_time.tzinfo is not None:
            latest_time = latest_time.replace(tzinfo=None)
        
        age_minutes = (now - latest_time).total_seconds() / 60
        logger.info(f"  Age: {age_minutes:.1f} minutes")
        
        if age_minutes <= 10:
            logger.info(f"  ✅ FRESH DATA")
            return True
        elif age_minutes <= 30:
            logger.info(f"  ✓ Acceptable ({age_minutes:.1f} min old)")
            return True
        else:
            logger.warning(f"  ⚠ Stale ({age_minutes:.1f} min old)")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


def main():
    """Test all three symbols with multi-provider setup"""
    logger.info("=" * 80)
    logger.info("MULTI-PROVIDER HYBRID CLIENT TEST")
    logger.info("=" * 80)
    logger.info(f"Current time: {datetime.now()}")
    logger.info("")
    
    # Show available providers
    logger.info("Available Providers:")
    logger.info(f"  ✓ Alpha Vantage: {ALPHA_VANTAGE_KEY[:10]}...")
    if TWELVE_DATA_KEY:
        logger.info(f"  ✓ Twelve Data: {TWELVE_DATA_KEY[:10]}...")
    else:
        logger.info(f"  ✗ Twelve Data: Not configured")
    logger.info(f"  ✓ yfinance: Always available (fallback)")
    logger.info("")
    
    results = {}
    
    # Test BTC (will use yfinance - best for crypto)
    logger.info("")
    results['BTC/USD'] = test_symbol_with_providers('BTC/USD', ALPHA_VANTAGE_KEY, TWELVE_DATA_KEY)
    
    # Wait between tests to respect rate limits
    import time
    time.sleep(15)
    
    # Test US30 (will use Alpha Vantage first)
    logger.info("")
    results['US30/USD'] = test_symbol_with_providers('US30/USD', ALPHA_VANTAGE_KEY, TWELVE_DATA_KEY)
    
    time.sleep(15)
    
    # Test XAU/USD (will use Alpha Vantage first)
    logger.info("")
    results['XAU/USD'] = test_symbol_with_providers('XAU/USD', ALPHA_VANTAGE_KEY, TWELVE_DATA_KEY)
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    for symbol, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{symbol}: {status}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("PROVIDER STRATEGY")
    logger.info("=" * 80)
    logger.info("")
    logger.info("BTC/USD:")
    logger.info("  Primary: yfinance (free, unlimited, good for crypto)")
    logger.info("  Fallback: Twelve Data → Alpha Vantage")
    logger.info("")
    logger.info("US30/USD:")
    logger.info("  Primary: Alpha Vantage (better for indices)")
    logger.info("  Fallback: Twelve Data → yfinance")
    logger.info("")
    logger.info("XAU/USD:")
    logger.info("  Primary: Alpha Vantage (better for forex)")
    logger.info("  Fallback: Twelve Data → yfinance")
    logger.info("")
    logger.info("Rate Limit Management:")
    logger.info("  - Alpha Vantage: 5 calls/min, 500/day")
    logger.info("  - Twelve Data: 8 calls/min, 800/day (if configured)")
    logger.info("  - yfinance: Unlimited (but delayed)")
    logger.info("  - Automatic fallback if rate limits hit")
    logger.info("")
    
    if not TWELVE_DATA_KEY:
        logger.info("💡 TIP: Get Twelve Data API key for better rate limits:")
        logger.info("   https://twelvedata.com/pricing")
        logger.info("   Then set: export TWELVE_DATA_KEY=your_key")
        logger.info("")
    
    logger.info("=" * 80)
    logger.info("NEXT STEPS")
    logger.info("=" * 80)
    
    if all(results.values()):
        logger.info("✅ All providers working!")
        logger.info("")
        logger.info("1. Update your scanner to use HybridDataClient")
        logger.info("2. Set scan interval to 5 minutes (to stay under rate limits)")
        logger.info("3. System will automatically use best provider for each asset")
        logger.info("4. Automatic fallback if any provider fails")
    else:
        logger.warning("⚠ Some tests failed - check logs above")
        logger.info("")
        logger.info("This may be due to:")
        logger.info("  - Markets being closed")
        logger.info("  - Rate limits hit")
        logger.info("  - Network issues")
        logger.info("")
        logger.info("The system will automatically fallback to working providers")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
