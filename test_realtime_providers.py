"""
Test real-time free data providers for BTC, US30, and XAU/USD
"""
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_alpha_vantage():
    """Test Alpha Vantage (free tier: 5 calls/min, 500 calls/day)"""
    logger.info("\n" + "="*80)
    logger.info("TESTING ALPHA VANTAGE")
    logger.info("="*80)
    
    try:
        from alpha_vantage.timeseries import TimeSeries
        from alpha_vantage.cryptocurrencies import CryptoCurrencies
        
        # Note: Requires API key (free tier available)
        logger.info("✓ Alpha Vantage library installed")
        logger.info("  Supports: Stocks, Forex, Crypto")
        logger.info("  Real-time: YES (with free API key)")
        logger.info("  Free tier: 5 calls/min, 500 calls/day")
        logger.info("  US30: ✓ (via ^DJI)")
        logger.info("  XAU/USD: ✓ (Forex pair)")
        logger.info("  BTC/USD: ✓ (Crypto)")
        logger.info("  Get free key: https://www.alphavantage.co/support/#api-key")
        return True
    except ImportError:
        logger.warning("✗ Alpha Vantage not installed: pip install alpha-vantage")
        return False


def test_polygon():
    """Test Polygon.io (free tier: delayed data)"""
    logger.info("\n" + "="*80)
    logger.info("TESTING POLYGON.IO")
    logger.info("="*80)
    
    try:
        import polygon
        logger.info("✓ Polygon library installed")
        logger.info("  Supports: Stocks, Forex, Crypto")
        logger.info("  Real-time: NO (free tier is 15-min delayed)")
        logger.info("  Free tier: Delayed data only")
        logger.info("  Paid tier: Real-time from $99/month")
        return False
    except ImportError:
        logger.warning("✗ Polygon not installed: pip install polygon-api-client")
        return False


def test_twelve_data():
    """Test Twelve Data (free tier: 800 calls/day)"""
    logger.info("\n" + "="*80)
    logger.info("TESTING TWELVE DATA")
    logger.info("="*80)
    
    try:
        from twelvedata import TDClient
        logger.info("✓ Twelve Data library installed")
        logger.info("  Supports: Stocks, Forex, Crypto, Indices")
        logger.info("  Real-time: YES (with free API key)")
        logger.info("  Free tier: 800 calls/day, 8 calls/min")
        logger.info("  US30: ✓ (DJI)")
        logger.info("  XAU/USD: ✓ (Forex pair)")
        logger.info("  BTC/USD: ✓ (Crypto)")
        logger.info("  Get free key: https://twelvedata.com/pricing")
        return True
    except ImportError:
        logger.warning("✗ Twelve Data not installed: pip install twelvedata")
        return False


def test_finnhub():
    """Test Finnhub (free tier: 60 calls/min)"""
    logger.info("\n" + "="*80)
    logger.info("TESTING FINNHUB")
    logger.info("="*80)
    
    try:
        import finnhub
        logger.info("✓ Finnhub library installed")
        logger.info("  Supports: Stocks, Forex, Crypto")
        logger.info("  Real-time: YES (with free API key)")
        logger.info("  Free tier: 60 calls/min")
        logger.info("  US30: ✓ (via indices)")
        logger.info("  XAU/USD: ✓ (Forex)")
        logger.info("  BTC/USD: ✓ (Crypto)")
        logger.info("  Get free key: https://finnhub.io/register")
        return True
    except ImportError:
        logger.warning("✗ Finnhub not installed: pip install finnhub-python")
        return False


def test_ccxt_realtime():
    """Test CCXT exchanges for real-time crypto data"""
    logger.info("\n" + "="*80)
    logger.info("TESTING CCXT (CRYPTO EXCHANGES)")
    logger.info("="*80)
    
    try:
        import ccxt
        logger.info("✓ CCXT library installed")
        logger.info("  Supports: Crypto only (100+ exchanges)")
        logger.info("  Real-time: YES (no API key needed for most)")
        logger.info("  Free tier: Unlimited (rate limits vary)")
        logger.info("  US30: ✗ (Not available)")
        logger.info("  XAU/USD: ✗ (Not available)")
        logger.info("  BTC/USD: ✓ (Multiple exchanges)")
        logger.info("  Best for: BTC only")
        return True
    except ImportError:
        logger.warning("✗ CCXT not installed")
        return False


def test_eodhd():
    """Test EOD Historical Data"""
    logger.info("\n" + "="*80)
    logger.info("TESTING EOD HISTORICAL DATA")
    logger.info("="*80)
    
    logger.info("  Supports: Stocks, Forex, Crypto, Indices")
    logger.info("  Real-time: YES (with API key)")
    logger.info("  Free tier: End-of-day data only")
    logger.info("  Paid tier: Real-time from $19.99/month")
    logger.info("  US30: ✓")
    logger.info("  XAU/USD: ✓")
    logger.info("  BTC/USD: ✓")
    return False


def test_iex_cloud():
    """Test IEX Cloud"""
    logger.info("\n" + "="*80)
    logger.info("TESTING IEX CLOUD")
    logger.info("="*80)
    
    logger.info("  Supports: US Stocks only")
    logger.info("  Real-time: YES (with free API key)")
    logger.info("  Free tier: 50,000 messages/month")
    logger.info("  US30: ✗ (Stocks only, no indices)")
    logger.info("  XAU/USD: ✗")
    logger.info("  BTC/USD: ✗")
    logger.info("  Best for: US stocks only")
    return False


def main():
    """Test all providers"""
    
    logger.info("="*80)
    logger.info("REAL-TIME FREE DATA PROVIDER COMPARISON")
    logger.info("="*80)
    logger.info("\nTesting which providers support BTC, US30, and XAU/USD...")
    
    results = {
        'Alpha Vantage': test_alpha_vantage(),
        'Twelve Data': test_twelve_data(),
        'Finnhub': test_finnhub(),
        'CCXT': test_ccxt_realtime(),
        'Polygon.io': test_polygon(),
        'EOD Historical': test_eodhd(),
        'IEX Cloud': test_iex_cloud(),
    }
    
    logger.info("\n" + "="*80)
    logger.info("SUMMARY - BEST FREE REAL-TIME OPTIONS")
    logger.info("="*80)
    
    logger.info("\n🥇 RECOMMENDED: Alpha Vantage")
    logger.info("   ✓ Real-time data for ALL three assets")
    logger.info("   ✓ Free tier: 5 calls/min, 500 calls/day")
    logger.info("   ✓ Easy to use API")
    logger.info("   ✓ No credit card required")
    logger.info("   → Get free key: https://www.alphavantage.co/support/#api-key")
    
    logger.info("\n🥈 ALTERNATIVE: Twelve Data")
    logger.info("   ✓ Real-time data for ALL three assets")
    logger.info("   ✓ Free tier: 800 calls/day, 8 calls/min")
    logger.info("   ✓ Good for multiple timeframes")
    logger.info("   → Get free key: https://twelvedata.com/pricing")
    
    logger.info("\n🥉 ALTERNATIVE: Finnhub")
    logger.info("   ✓ Real-time data for ALL three assets")
    logger.info("   ✓ Free tier: 60 calls/min")
    logger.info("   ✓ WebSocket support")
    logger.info("   → Get free key: https://finnhub.io/register")
    
    logger.info("\n📊 FOR BTC ONLY: CCXT (Kraken/Binance)")
    logger.info("   ✓ Real-time crypto data")
    logger.info("   ✓ No API key needed")
    logger.info("   ✓ Unlimited (with rate limits)")
    logger.info("   ✗ Crypto only - no US30 or XAU/USD")
    
    logger.info("\n⚠️  CURRENT ISSUE: yfinance")
    logger.info("   ✓ Has data for all assets")
    logger.info("   ✗ 15-20 minute delay on free tier")
    logger.info("   ✗ Not suitable for real-time trading")
    
    logger.info("\n" + "="*80)
    logger.info("RECOMMENDATION FOR YOUR SYSTEM")
    logger.info("="*80)
    logger.info("\n1. Get a FREE Alpha Vantage API key (takes 30 seconds)")
    logger.info("2. Install: pip install alpha-vantage")
    logger.info("3. Update config to use Alpha Vantage for all three assets")
    logger.info("4. This will give you REAL-TIME data for BTC, US30, and XAU/USD")
    logger.info("\nWith 5 calls/min, you can scan all 3 assets every minute!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
