"""
Comprehensive Data Feed Diagnostic Test
Tests what symbols are available and verifies all data is being pulled correctly
"""
import logging
import ccxt
from datetime import datetime, timedelta
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_exchange_symbols():
    """Check what symbols are actually available on Kraken"""
    logger.info("=" * 80)
    logger.info("CHECKING AVAILABLE SYMBOLS ON KRAKEN")
    logger.info("=" * 80)
    
    try:
        exchange = ccxt.kraken()
        markets = exchange.load_markets()
        
        # Check for our target symbols
        target_symbols = [
            'BTC/USD', 'BTC/USDT', 'BTCUSD',
            'XAU/USD', 'XAUUSD', 'GOLD/USD',
            'US30/USD', 'US30USD', 'DJI/USD', 'DJIA/USD'
        ]
        
        logger.info("\nSearching for target symbols:")
        found_symbols = {}
        
        for target in target_symbols:
            if target in markets:
                logger.info(f"  ✓ Found: {target}")
                found_symbols[target] = markets[target]
            else:
                logger.info(f"  ✗ Not found: {target}")
        
        # Search for similar symbols
        logger.info("\nSearching for BTC-related symbols:")
        btc_symbols = [s for s in markets.keys() if 'BTC' in s and ('USD' in s or 'USDT' in s)]
        for sym in btc_symbols[:10]:  # Show first 10
            logger.info(f"  - {sym}")
        
        logger.info("\nSearching for Gold/XAU-related symbols:")
        gold_symbols = [s for s in markets.keys() if 'XAU' in s or 'GOLD' in s]
        for sym in gold_symbols:
            logger.info(f"  - {sym}")
        
        logger.info("\nSearching for US30/Dow-related symbols:")
        us30_symbols = [s for s in markets.keys() if any(x in s for x in ['US30', 'DJI', 'DJIA', 'DOW'])]
        for sym in us30_symbols:
            logger.info(f"  - {sym}")
        
        return found_symbols
        
    except Exception as e:
        logger.error(f"Error checking symbols: {e}", exc_info=True)
        return {}


def test_data_freshness(symbol='BTC/USD', timeframe='5m'):
    """Test if data is fresh and up-to-date"""
    logger.info("=" * 80)
    logger.info(f"TESTING DATA FRESHNESS FOR {symbol}")
    logger.info("=" * 80)
    
    try:
        exchange = ccxt.kraken()
        
        # Fetch recent candles
        logger.info(f"\nFetching {timeframe} candles...")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=10)
        
        if not ohlcv:
            logger.error("No data received!")
            return False
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        logger.info(f"\n✓ Received {len(df)} candles")
        logger.info(f"\nLatest candle:")
        latest = df.iloc[-1]
        logger.info(f"  Timestamp: {latest['timestamp']}")
        logger.info(f"  Close: ${latest['close']:.2f}")
        logger.info(f"  Volume: {latest['volume']:.2f}")
        
        # Check freshness
        now = datetime.now()
        latest_time = latest['timestamp'].to_pydatetime()
        
        # Remove timezone info if present for comparison
        if latest_time.tzinfo is not None:
            latest_time = latest_time.replace(tzinfo=None)
        
        age_minutes = (now - latest_time).total_seconds() / 60
        
        logger.info(f"\nData Age Analysis:")
        logger.info(f"  Current time: {now}")
        logger.info(f"  Latest data: {latest_time}")
        logger.info(f"  Age: {age_minutes:.1f} minutes")
        
        if age_minutes <= 10:
            logger.info(f"  ✓ Data is FRESH (< 10 minutes old)")
            return True
        elif age_minutes <= 30:
            logger.warning(f"  ⚠ Data is STALE ({age_minutes:.1f} minutes old)")
            return False
        else:
            logger.error(f"  ✗ Data is VERY STALE ({age_minutes:.1f} minutes old)")
            return False
            
    except Exception as e:
        logger.error(f"Error testing data freshness: {e}", exc_info=True)
        return False


def test_complete_data_fields(symbol='BTC/USD', timeframe='5m'):
    """Verify all required data fields are present"""
    logger.info("=" * 80)
    logger.info(f"TESTING COMPLETE DATA FIELDS FOR {symbol}")
    logger.info("=" * 80)
    
    try:
        exchange = ccxt.kraken()
        
        # Fetch data
        logger.info(f"\nFetching {timeframe} candles...")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        logger.info(f"✓ Received {len(df)} candles")
        
        # Check for required fields
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        logger.info(f"\nChecking required fields:")
        
        all_present = True
        for field in required_fields:
            if field in df.columns:
                non_null = df[field].notna().sum()
                logger.info(f"  ✓ {field}: {non_null}/{len(df)} values present")
                
                if field != 'timestamp':
                    logger.info(f"    Min: {df[field].min():.2f}, Max: {df[field].max():.2f}, Avg: {df[field].mean():.2f}")
            else:
                logger.error(f"  ✗ {field}: MISSING")
                all_present = False
        
        # Check for zero/null values
        logger.info(f"\nData Quality Checks:")
        
        zero_volumes = (df['volume'] == 0).sum()
        if zero_volumes > 0:
            logger.warning(f"  ⚠ Found {zero_volumes} candles with zero volume")
        else:
            logger.info(f"  ✓ All candles have non-zero volume")
        
        null_prices = df[['open', 'high', 'low', 'close']].isnull().sum().sum()
        if null_prices > 0:
            logger.error(f"  ✗ Found {null_prices} null price values")
            all_present = False
        else:
            logger.info(f"  ✓ All price fields are populated")
        
        # Check price consistency
        invalid_candles = ((df['high'] < df['low']) | 
                          (df['high'] < df['open']) | 
                          (df['high'] < df['close']) |
                          (df['low'] > df['open']) |
                          (df['low'] > df['close'])).sum()
        
        if invalid_candles > 0:
            logger.error(f"  ✗ Found {invalid_candles} candles with invalid OHLC relationships")
            all_present = False
        else:
            logger.info(f"  ✓ All candles have valid OHLC relationships")
        
        return all_present
        
    except Exception as e:
        logger.error(f"Error testing data fields: {e}", exc_info=True)
        return False


def main():
    """Run all diagnostic tests"""
    logger.info("=" * 80)
    logger.info("DATA FEED COMPREHENSIVE DIAGNOSTIC")
    logger.info("=" * 80)
    logger.info("")
    
    # Test 1: Check available symbols
    found_symbols = test_exchange_symbols()
    
    # Test 2: Test data freshness for BTC
    logger.info("\n")
    if 'BTC/USD' in found_symbols:
        btc_fresh = test_data_freshness('BTC/USD', '5m')
    elif 'BTC/USDT' in found_symbols:
        btc_fresh = test_data_freshness('BTC/USDT', '5m')
    else:
        logger.error("No BTC symbol found to test!")
        btc_fresh = False
    
    # Test 3: Test complete data fields
    logger.info("\n")
    if 'BTC/USD' in found_symbols:
        btc_complete = test_complete_data_fields('BTC/USD', '5m')
    elif 'BTC/USDT' in found_symbols:
        btc_complete = test_complete_data_fields('BTC/USDT', '5m')
    else:
        btc_complete = False
    
    # Summary
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Symbols found: {len(found_symbols)}")
    logger.info(f"Data freshness: {'✓ PASS' if btc_fresh else '✗ FAIL'}")
    logger.info(f"Data completeness: {'✓ PASS' if btc_complete else '✗ FAIL'}")
    logger.info("")
    
    if not found_symbols:
        logger.error("⚠️  CRITICAL: No target symbols found on exchange!")
        logger.error("   US30 is NOT available on Kraken - need to use a different exchange")
    
    if not btc_fresh:
        logger.warning("⚠️  WARNING: Data is stale - may be outside trading hours")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
