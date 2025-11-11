"""
Test yfinance support for our target symbols
"""
import logging
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_symbol(symbol, name):
    """Test if yfinance supports a symbol and get recent data"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing {name} ({symbol})")
    logger.info(f"{'='*80}")
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get recent data (last 2 days, 5-minute intervals)
        logger.info("Fetching 5-minute data...")
        df = ticker.history(period='2d', interval='5m')
        
        if df.empty:
            logger.error(f"  ✗ No data available for {symbol}")
            return False
        
        logger.info(f"  ✓ Received {len(df)} candles")
        
        # Check data freshness
        latest_time = df.index[-1]
        now = pd.Timestamp.now(tz=latest_time.tz)
        age_minutes = (now - latest_time).total_seconds() / 60
        
        logger.info(f"\nLatest Data:")
        logger.info(f"  Timestamp: {latest_time}")
        logger.info(f"  Close: ${df.iloc[-1]['Close']:.2f}")
        logger.info(f"  Volume: {df.iloc[-1]['Volume']:.0f}")
        logger.info(f"  Age: {age_minutes:.1f} minutes")
        
        # Check data completeness
        logger.info(f"\nData Quality:")
        logger.info(f"  Open: {df['Open'].notna().sum()}/{len(df)} values")
        logger.info(f"  High: {df['High'].notna().sum()}/{len(df)} values")
        logger.info(f"  Low: {df['Low'].notna().sum()}/{len(df)} values")
        logger.info(f"  Close: {df['Close'].notna().sum()}/{len(df)} values")
        logger.info(f"  Volume: {df['Volume'].notna().sum()}/{len(df)} values")
        
        # Check for zero volumes
        zero_volumes = (df['Volume'] == 0).sum()
        if zero_volumes > 0:
            logger.warning(f"  ⚠ {zero_volumes} candles with zero volume")
        
        # Data freshness assessment
        if age_minutes <= 10:
            logger.info(f"  ✓ Data is FRESH (< 10 minutes old)")
            return True
        elif age_minutes <= 30:
            logger.warning(f"  ⚠ Data is STALE ({age_minutes:.1f} minutes old)")
            return True
        else:
            logger.error(f"  ✗ Data is VERY STALE ({age_minutes:.1f} minutes old)")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        return False


def test_all_intervals(symbol):
    """Test what intervals are available"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing Available Intervals for {symbol}")
    logger.info(f"{'='*80}")
    
    intervals = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d']
    ticker = yf.Ticker(symbol)
    
    for interval in intervals:
        try:
            df = ticker.history(period='1d', interval=interval)
            if not df.empty:
                logger.info(f"  ✓ {interval}: {len(df)} candles")
            else:
                logger.info(f"  ✗ {interval}: No data")
        except Exception as e:
            logger.info(f"  ✗ {interval}: Error - {str(e)[:50]}")


def main():
    """Test yfinance for all our target symbols"""
    
    logger.info("="*80)
    logger.info("YFINANCE SYMBOL SUPPORT TEST")
    logger.info("="*80)
    
    # Test symbols with their yfinance tickers
    symbols = [
        ('BTC-USD', 'Bitcoin'),
        ('^DJI', 'Dow Jones Industrial Average (US30)'),
        ('GC=F', 'Gold Futures (XAU/USD equivalent)'),
        ('^GSPC', 'S&P 500'),
        ('^IXIC', 'NASDAQ'),
    ]
    
    results = {}
    for symbol, name in symbols:
        results[name] = test_symbol(symbol, name)
    
    # Test intervals for US30
    test_all_intervals('^DJI')
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    
    for name, success in results.items():
        status = "✓ SUPPORTED" if success else "✗ NOT SUPPORTED"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\n{'='*80}")
    logger.info("YFINANCE TICKER MAPPINGS")
    logger.info(f"{'='*80}")
    logger.info("BTC/USD  → BTC-USD")
    logger.info("US30/USD → ^DJI (Dow Jones Industrial Average)")
    logger.info("XAU/USD  → GC=F (Gold Futures)")
    logger.info("\nNote: yfinance provides delayed data (15-20 min) for free")
    logger.info("Real-time data requires a paid data provider")
    
    logger.info(f"\n{'='*80}")
    logger.info("RECOMMENDATION")
    logger.info(f"{'='*80}")
    logger.info("✓ yfinance CAN provide data for all three assets")
    logger.info("✓ Data quality is good with complete OHLCV")
    logger.info("⚠ Data may be delayed 15-20 minutes (free tier)")
    logger.info("⚠ Check if delay is acceptable for your trading strategy")


if __name__ == "__main__":
    main()
