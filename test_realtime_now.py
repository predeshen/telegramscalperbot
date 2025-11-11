"""
Test what data sources are actually giving us real-time data RIGHT NOW
"""
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_yfinance():
    """Test yfinance current data"""
    logger.info("\n" + "="*80)
    logger.info("TESTING YFINANCE")
    logger.info("="*80)
    
    try:
        import yfinance as yf
        
        symbols = [
            ('BTC-USD', 'Bitcoin'),
            ('^DJI', 'US30'),
            ('GC=F', 'Gold'),
        ]
        
        for ticker, name in symbols:
            logger.info(f"\n{name} ({ticker}):")
            data = yf.Ticker(ticker)
            hist = data.history(period='1d', interval='1m')
            
            if not hist.empty:
                latest = hist.index[-1]
                now = datetime.now()
                
                # Handle timezone
                if hasattr(latest, 'tz_localize'):
                    latest = latest.tz_localize(None)
                elif hasattr(latest, 'tz_convert'):
                    latest = latest.tz_convert(None).replace(tzinfo=None)
                
                age_seconds = (now - latest).total_seconds()
                logger.info(f"  Latest: {latest}")
                logger.info(f"  Age: {age_seconds/60:.1f} minutes")
                logger.info(f"  Price: ${hist.iloc[-1]['Close']:.2f}")
                
                if age_seconds < 300:  # 5 minutes
                    logger.info(f"  ✓ REAL-TIME")
                else:
                    logger.info(f"  ✗ STALE")
            else:
                logger.info(f"  ✗ No data")
                
    except Exception as e:
        logger.error(f"Error: {e}")


def test_ccxt():
    """Test CCXT for BTC"""
    logger.info("\n" + "="*80)
    logger.info("TESTING CCXT (KRAKEN) FOR BTC")
    logger.info("="*80)
    
    try:
        import ccxt
        import pandas as pd
        
        exchange = ccxt.kraken()
        
        for symbol in ['BTC/USD', 'BTC/USDT']:
            logger.info(f"\n{symbol}:")
            ohlcv = exchange.fetch_ohlcv(symbol, '1m', limit=5)
            
            if ohlcv:
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                latest = df.iloc[-1]['timestamp'].to_pydatetime()
                now = datetime.now()
                age_seconds = (now - latest).total_seconds()
                
                logger.info(f"  Latest: {latest}")
                logger.info(f"  Age: {age_seconds/60:.1f} minutes")
                logger.info(f"  Price: ${df.iloc[-1]['close']:.2f}")
                
                if age_seconds < 300:  # 5 minutes
                    logger.info(f"  ✓ REAL-TIME")
                else:
                    logger.info(f"  ✗ STALE")
            else:
                logger.info(f"  ✗ No data")
                
    except Exception as e:
        logger.error(f"Error: {e}")


def test_broker_apis():
    """Check if user has broker API access"""
    logger.info("\n" + "="*80)
    logger.info("BROKER API OPTIONS")
    logger.info("="*80)
    
    logger.info("\nIf you're actively trading these markets, you likely have:")
    logger.info("1. A broker account (Interactive Brokers, TD Ameritrade, etc.)")
    logger.info("2. API access to that broker")
    logger.info("3. Real-time data feed from that broker")
    logger.info("\nDo you have API credentials for your broker?")
    logger.info("Common brokers with APIs:")
    logger.info("  - Interactive Brokers (IBKR)")
    logger.info("  - TD Ameritrade")
    logger.info("  - Alpaca")
    logger.info("  - MetaTrader 4/5")
    logger.info("  - TradingView")


def main():
    """Run all tests"""
    logger.info("="*80)
    logger.info("REAL-TIME DATA TEST - CURRENT MARKET CONDITIONS")
    logger.info("="*80)
    logger.info(f"Current time: {datetime.now()}")
    
    test_yfinance()
    test_ccxt()
    test_broker_apis()
    
    logger.info("\n" + "="*80)
    logger.info("CONCLUSION")
    logger.info("="*80)
    logger.info("\nIf you're actively trading and seeing real-time prices in your")
    logger.info("trading platform, but our tests show stale data, then:")
    logger.info("")
    logger.info("1. Free data providers (yfinance) have significant delays")
    logger.info("2. You need to use your BROKER'S API for real-time data")
    logger.info("3. Tell me which broker you use, and I'll integrate their API")
    logger.info("")
    logger.info("Which broker/platform are you trading with?")
    logger.info("  - MetaTrader 4/5?")
    logger.info("  - Interactive Brokers?")
    logger.info("  - TD Ameritrade?")
    logger.info("  - Other?")
    logger.info("="*80)


if __name__ == "__main__":
    main()
