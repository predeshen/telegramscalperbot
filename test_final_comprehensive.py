"""
FINAL COMPREHENSIVE TEST
Tests all data providers, all assets, all timeframes with proper timezone handling
"""
import logging
from datetime import datetime, timezone
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys
ALPHA_VANTAGE_KEY = "66IUJDWBSTV9U220"
TWELVE_DATA_KEY = "a4f7101c037f4cf5949a1be62973283f"


def test_yfinance_freshness():
    """Test yfinance data freshness"""
    logger.info("=" * 80)
    logger.info("TESTING YFINANCE FRESHNESS")
    logger.info("=" * 80)
    
    try:
        import yfinance as yf
        import pandas as pd
        
        symbols = [
            ('BTC-USD', 'Bitcoin'),
            ('^DJI', 'US30'),
            ('GC=F', 'Gold'),
        ]
        
        results = {}
        
        for ticker, name in symbols:
            logger.info(f"\n{name} ({ticker}):")
            
            try:
                data = yf.Ticker(ticker)
                hist = data.history(period='1d', interval='1m')
                
                if hist.empty:
                    logger.warning(f"  ✗ No data")
                    results[name] = False
                    continue
                
                latest = hist.index[-1]
                now_utc = datetime.now(timezone.utc)
                
                # Convert to UTC if needed
                if latest.tzinfo is None:
                    latest = latest.replace(tzinfo=timezone.utc)
                
                age_seconds = (now_utc - latest).total_seconds()
                age_minutes = age_seconds / 60
                
                logger.info(f"  Latest: {latest}")
                logger.info(f"  Age: {age_minutes:.1f} minutes")
                logger.info(f"  Price: ${hist.iloc[-1]['Close']:.2f}")
                
                if age_minutes < 5:
                    logger.info(f"  ✅ REAL-TIME")
                    results[name] = True
                elif age_minutes < 30:
                    logger.info(f"  ✓ FRESH")
                    results[name] = True
                else:
                    logger.warning(f"  ⚠ STALE ({age_minutes:.1f} min)")
                    results[name] = False
                    
            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                results[name] = False
        
        return results
        
    except Exception as e:
        logger.error(f"Error testing yfinance: {e}")
        return {}


def test_provider_freshness(provider_name, symbol, timeframe='5m'):
    """Test a specific provider's data freshness"""
    try:
        from src.hybrid_data_client import HybridDataClient
        
        # Force specific provider
        client = HybridDataClient(
            symbol=symbol,
            timeframes=[timeframe],
            buffer_size=10,
            alpha_vantage_key=ALPHA_VANTAGE_KEY,
            twelve_data_key=TWELVE_DATA_KEY,
            preferred_provider=provider_name
        )
        
        if not client.connect():
            return None, "Connection failed"
        
        data = client.get_latest_candles(timeframe, count=5)
        
        if data.empty:
            return None, "No data"
        
        latest = data.iloc[-1]
        latest_time = latest['timestamp']
        
        # Convert to UTC
        if hasattr(latest_time, 'to_pydatetime'):
            latest_time = latest_time.to_pydatetime()
        
        if latest_time.tzinfo is None:
            latest_time = latest_time.replace(tzinfo=timezone.utc)
        elif latest_time.tzinfo != timezone.utc:
            latest_time = latest_time.astimezone(timezone.utc)
        
        now_utc = datetime.now(timezone.utc)
        age_seconds = (now_utc - latest_time).total_seconds()
        age_minutes = age_seconds / 60
        
        return age_minutes, f"${latest['close']:.2f}"
        
    except Exception as e:
        return None, str(e)


def test_all_providers():
    """Test all providers for all assets"""
    logger.info("=" * 80)
    logger.info("TESTING ALL PROVIDERS - ALL ASSETS")
    logger.info("=" * 80)
    
    test_matrix = [
        ('BTC/USD', 'kraken', '5m'),
        ('BTC/USD', 'yfinance', '5m'),
        ('US30/USD', 'alpha_vantage', '5m'),
        ('US30/USD', 'twelve_data', '5m'),
        ('US30/USD', 'yfinance', '5m'),
        ('XAU/USD', 'alpha_vantage', '5m'),
        ('XAU/USD', 'twelve_data', '5m'),
        ('XAU/USD', 'yfinance', '5m'),
    ]
    
    results = {}
    
    for symbol, provider, timeframe in test_matrix:
        logger.info(f"\n{'─' * 80}")
        logger.info(f"{symbol} via {provider.upper()}")
        logger.info(f"{'─' * 80}")
        
        age_minutes, info = test_provider_freshness(provider, symbol, timeframe)
        
        if age_minutes is not None:
            logger.info(f"  Age: {age_minutes:.1f} minutes")
            logger.info(f"  Price: {info}")
            
            if age_minutes < 5:
                logger.info(f"  ✅ REAL-TIME")
                status = "REAL-TIME"
            elif age_minutes < 30:
                logger.info(f"  ✓ FRESH")
                status = "FRESH"
            elif age_minutes < 120:
                logger.info(f"  ⚠ ACCEPTABLE")
                status = "ACCEPTABLE"
            else:
                logger.warning(f"  ✗ STALE")
                status = "STALE"
            
            results[f"{symbol}_{provider}"] = {
                'age': age_minutes,
                'status': status,
                'price': info
            }
        else:
            logger.error(f"  ✗ FAILED: {info}")
            results[f"{symbol}_{provider}"] = {
                'age': None,
                'status': 'FAILED',
                'price': info
            }
        
        # Wait between tests to respect rate limits
        time.sleep(3)
    
    return results


def test_all_timeframes():
    """Test all timeframes for each asset"""
    logger.info("=" * 80)
    logger.info("TESTING ALL TIMEFRAMES")
    logger.info("=" * 80)
    
    test_config = [
        ('BTC/USD', ['1m', '5m', '15m', '1h', '4h'], 'kraken'),
        ('US30/USD', ['5m', '15m', '1h', '4h'], 'alpha_vantage'),
        ('XAU/USD', ['5m', '15m', '1h', '4h'], 'alpha_vantage'),
    ]
    
    results = {}
    
    for symbol, timeframes, provider in test_config:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"{symbol} - ALL TIMEFRAMES")
        logger.info(f"{'=' * 80}")
        
        symbol_results = {}
        
        for tf in timeframes:
            logger.info(f"\n  Testing {tf}...")
            
            age_minutes, info = test_provider_freshness(provider, symbol, tf)
            
            if age_minutes is not None:
                logger.info(f"    Age: {age_minutes:.1f} min | Price: {info}")
                symbol_results[tf] = age_minutes < 120  # Pass if < 2 hours
            else:
                logger.error(f"    ✗ Failed: {info}")
                symbol_results[tf] = False
            
            time.sleep(2)
        
        results[symbol] = symbol_results
        
        # Summary
        passed = sum(symbol_results.values())
        total = len(symbol_results)
        logger.info(f"\n  Summary: {passed}/{total} timeframes passed")
    
    return results


def main():
    """Run all comprehensive tests"""
    logger.info("=" * 80)
    logger.info("FINAL COMPREHENSIVE TEST SUITE")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.now(timezone.utc)} UTC")
    logger.info("")
    
    all_results = {}
    
    # Test 1: yfinance freshness
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: YFINANCE FRESHNESS")
    logger.info("=" * 80)
    yf_results = test_yfinance_freshness()
    all_results['yfinance'] = yf_results
    
    time.sleep(5)
    
    # Test 2: All providers
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: ALL PROVIDERS")
    logger.info("=" * 80)
    provider_results = test_all_providers()
    all_results['providers'] = provider_results
    
    time.sleep(5)
    
    # Test 3: All timeframes
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: ALL TIMEFRAMES")
    logger.info("=" * 80)
    timeframe_results = test_all_timeframes()
    all_results['timeframes'] = timeframe_results
    
    # Final Summary
    logger.info("\n" + "=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    
    logger.info("\n📊 YFINANCE RESULTS:")
    for asset, passed in yf_results.items():
        status = "✅" if passed else "❌"
        logger.info(f"  {status} {asset}")
    
    logger.info("\n📊 PROVIDER RESULTS:")
    for key, result in provider_results.items():
        status_icon = {
            'REAL-TIME': '✅',
            'FRESH': '✓',
            'ACCEPTABLE': '⚠',
            'STALE': '✗',
            'FAILED': '❌'
        }.get(result['status'], '?')
        logger.info(f"  {status_icon} {key}: {result['status']} ({result.get('age', 'N/A')} min)")
    
    logger.info("\n📊 TIMEFRAME RESULTS:")
    for symbol, tfs in timeframe_results.items():
        passed = sum(tfs.values())
        total = len(tfs)
        logger.info(f"  {symbol}: {passed}/{total} passed")
    
    # Overall assessment
    logger.info("\n" + "=" * 80)
    logger.info("PRODUCTION READINESS ASSESSMENT")
    logger.info("=" * 80)
    
    yf_pass_rate = sum(yf_results.values()) / len(yf_results) * 100 if yf_results else 0
    provider_pass_rate = sum(1 for r in provider_results.values() if r['status'] in ['REAL-TIME', 'FRESH', 'ACCEPTABLE']) / len(provider_results) * 100 if provider_results else 0
    
    logger.info(f"\nyfinance Pass Rate: {yf_pass_rate:.0f}%")
    logger.info(f"Provider Pass Rate: {provider_pass_rate:.0f}%")
    
    if provider_pass_rate >= 80:
        logger.info("\n✅ SYSTEM IS PRODUCTION READY!")
        logger.info("\nRecommendations:")
        logger.info("  • Deploy to Google Cloud VM")
        logger.info("  • Use Kraken for BTC (real-time)")
        logger.info("  • Use Alpha Vantage for US30 (primary)")
        logger.info("  • Use Twelve Data for XAU (primary)")
        logger.info("  • yfinance as fallback for all")
        logger.info("  • Set scan interval to 5 minutes")
    else:
        logger.warning("\n⚠️ SOME PROVIDERS NEED ATTENTION")
        logger.info("\nCheck:")
        logger.info("  • API keys are valid")
        logger.info("  • Rate limits not exceeded")
        logger.info("  • Markets are open for testing")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"End Time: {datetime.now(timezone.utc)} UTC")
    logger.info("=" * 80)
    
    return provider_pass_rate >= 80


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
