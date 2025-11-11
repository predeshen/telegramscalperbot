"""
Test the hybrid data client system
"""
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.hybrid_data_client import HybridDataClient


def test_symbol(symbol, alpha_key=None):
    """Test a symbol with the hybrid client"""
    logger.info("=" * 80)
    logger.info(f"TESTING {symbol}")
    logger.info("=" * 80)
    
    try:
        # Initialize client
        client = HybridDataClient(
            symbol=symbol,
            timeframes=['5m'],
            buffer_size=100,
            alpha_vantage_key=alpha_key
        )
        
        # Show client info
        info = client.get_client_info()
        logger.info(f"Client Type: {info['client_type']}")
        logger.info(f"YFinance Ticker: {info['yfinance_ticker']}")
        
        # Connect
        logger.info("\nConnecting...")
        if not client.connect():
            logger.error("✗ Failed to connect")
            return False
        
        logger.info("✓ Connected successfully")
        
        # Fetch data
        logger.info("\nFetching 5m candles...")
        data = client.get_latest_candles('5m', count=100)
        
        if data.empty:
            logger.error("✗ No data received")
            return False
        
        logger.info(f"✓ Received {len(data)} candles")
        
        # Show latest data
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
            logger.info("  ✓ Data is FRESH")
            return True
        else:
            logger.warning(f"  ⚠ Data is {age_minutes:.1f} minutes old")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error testing {symbol}: {e}", exc_info=True)
        return False


def main():
    """Test all three symbols with yfinance"""
    logger.info("=" * 80)
    logger.info("HYBRID DATA CLIENT TEST (YFINANCE)")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Using yfinance for all symbols - no API key needed!")
    logger.info("Data delay: ~3 minutes (acceptable for 2-minute scans)")
    logger.info("")
    
    results = {}
    
    # Test BTC
    logger.info("")
    results['BTC/USD'] = test_symbol('BTC/USD')
    
    # Test US30
    logger.info("")
    results['US30/USD'] = test_symbol('US30/USD')
    
    # Test XAU/USD
    logger.info("")
    results['XAU/USD'] = test_symbol('XAU/USD')
    
    # Summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    for symbol, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{symbol}: {status}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)
    
    if all(results.values()):
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("")
        logger.info("✓ yfinance provides data for all three assets")
        logger.info("✓ No API key required")
        logger.info("✓ Data is fresh enough for 2-minute scans")
        logger.info("✓ Simple and reliable")
        logger.info("")
        logger.info("NEXT STEP: Update your main scanner to use HybridDataClient")
    else:
        logger.warning("⚠ Some tests failed - check logs above")
        logger.info("")
        logger.info("This may be due to:")
        logger.info("  - Markets being closed (US30 trades 9:30-16:00 ET)")
        logger.info("  - Network issues")
        logger.info("  - yfinance API issues")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
