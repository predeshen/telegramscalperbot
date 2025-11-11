"""
Test Alpha Vantage with real API key to verify real-time data
"""
import logging
import requests
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

API_KEY = "66IUJDWBSTV9U220"


def test_alpha_vantage_symbol(symbol, function, from_symbol=None, to_symbol=None):
    """Test Alpha Vantage for a symbol"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing {symbol}")
    logger.info(f"{'='*80}")
    
    try:
        base_url = "https://www.alphavantage.co/query"
        
        # Build params based on function type
        if function == 'FX_INTRADAY':
            params = {
                'function': function,
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'interval': '5min',
                'apikey': API_KEY
            }
        else:
            params = {
                'function': function,
                'symbol': symbol,
                'interval': '5min',
                'apikey': API_KEY
            }
        
        logger.info(f"Fetching data...")
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"✗ HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        # Check for errors
        if 'Error Message' in data:
            logger.error(f"✗ Error: {data['Error Message']}")
            return False
        
        if 'Note' in data:
            logger.warning(f"⚠ Rate limit: {data['Note']}")
            return False
        
        # Find time series key
        time_series_key = None
        for key in data.keys():
            if 'Time Series' in key:
                time_series_key = key
                break
        
        if not time_series_key:
            logger.error(f"✗ No time series data. Keys: {list(data.keys())}")
            return False
        
        time_series = data[time_series_key]
        
        # Get latest data point
        timestamps = sorted(time_series.keys(), reverse=True)
        latest_time_str = timestamps[0]
        latest_data = time_series[latest_time_str]
        
        # Parse timestamp
        latest_time = pd.to_datetime(latest_time_str)
        now = pd.Timestamp.now()
        
        # Calculate age
        age_seconds = (now - latest_time).total_seconds()
        age_minutes = age_seconds / 60
        
        # Get price
        close_key = '4. close' if '4. close' in latest_data else 'close'
        price = float(latest_data[close_key])
        
        logger.info(f"✓ Data received")
        logger.info(f"  Latest time: {latest_time}")
        logger.info(f"  Current time: {now}")
        logger.info(f"  Age: {age_minutes:.1f} minutes ({age_seconds:.0f} seconds)")
        logger.info(f"  Price: ${price:.2f}")
        
        if age_minutes <= 5:
            logger.info(f"  ✅ REAL-TIME DATA!")
            return True
        elif age_minutes <= 15:
            logger.info(f"  ✓ Fresh data (< 15 min)")
            return True
        else:
            logger.warning(f"  ⚠ Stale data ({age_minutes:.1f} min old)")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


def main():
    """Test all three assets with Alpha Vantage"""
    logger.info("="*80)
    logger.info("ALPHA VANTAGE REAL-TIME DATA TEST")
    logger.info("="*80)
    logger.info(f"API Key: {API_KEY}")
    logger.info(f"Current time: {datetime.now()}")
    logger.info("")
    
    results = {}
    
    # Test US30 (Dow Jones)
    logger.info("\n" + "="*80)
    logger.info("1. TESTING US30 (DOW JONES)")
    logger.info("="*80)
    results['US30'] = test_alpha_vantage_symbol('DJI', 'TIME_SERIES_INTRADAY')
    
    # Wait a bit to respect rate limits
    import time
    time.sleep(15)
    
    # Test XAU/USD (Gold)
    logger.info("\n" + "="*80)
    logger.info("2. TESTING XAU/USD (GOLD)")
    logger.info("="*80)
    results['XAU/USD'] = test_alpha_vantage_symbol('XAUUSD', 'FX_INTRADAY', 'XAU', 'USD')
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    for symbol, success in results.items():
        status = "✅ REAL-TIME" if success else "❌ STALE/FAILED"
        logger.info(f"{symbol}: {status}")
    
    logger.info("\n" + "="*80)
    logger.info("NEXT STEPS")
    logger.info("="*80)
    
    if all(results.values()):
        logger.info("✅ Alpha Vantage is providing REAL-TIME data!")
        logger.info("")
        logger.info("Now we'll:")
        logger.info("1. Update config.json with your API key")
        logger.info("2. Configure hybrid client to use Alpha Vantage for US30/XAU")
        logger.info("3. Keep using CCXT/Kraken for BTC (it's free and real-time)")
        logger.info("")
        logger.info("Rate limits: 5 calls/min, 500 calls/day")
        logger.info("Your usage: 2 assets × 1 call/2min = well within limits!")
    else:
        logger.warning("⚠ Some tests failed")
        logger.info("This could be due to:")
        logger.info("  - Markets being closed")
        logger.info("  - API rate limits")
        logger.info("  - Network issues")
    
    logger.info("="*80)


if __name__ == "__main__":
    main()
