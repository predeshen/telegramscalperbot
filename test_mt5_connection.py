"""
Test MT5 connection and data feed
"""
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MT5 credentials
MT5_ACCOUNTS = {
    'vantage': {
        'account': 19002423,
        'password': '239D8cc2#',
        'server': 'VantageInternational-Live 10'
    },
    'hfm': {
        'account': 54653113,
        'password': '239D8cc2#',
        'server': 'HFMarketsSA-Live2 Server'
    }
}


def test_mt5_basic():
    """Test basic MT5 connection"""
    logger.info("="*80)
    logger.info("TESTING MT5 BASIC CONNECTION")
    logger.info("="*80)
    
    try:
        import MetaTrader5 as mt5
        
        # Initialize MT5
        if not mt5.initialize():
            logger.error(f"✗ MT5 initialize() failed: {mt5.last_error()}")
            logger.info("\nMake sure:")
            logger.info("1. MetaTrader 5 terminal is installed")
            logger.info("2. MT5 terminal is running")
            logger.info("3. You're logged into an account")
            return False
        
        logger.info("✓ MT5 initialized successfully")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            logger.warning("⚠ Not logged in to any account")
            logger.info("Please log in to MT5 terminal manually, or provide credentials")
        else:
            logger.info(f"✓ Connected to account:")
            logger.info(f"  Login: {account_info.login}")
            logger.info(f"  Server: {account_info.server}")
            logger.info(f"  Balance: ${account_info.balance:.2f}")
            logger.info(f"  Leverage: 1:{account_info.leverage}")
        
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info:
            logger.info(f"\n✓ Terminal info:")
            logger.info(f"  Build: {terminal_info.build}")
            logger.info(f"  Connected: {terminal_info.connected}")
        
        mt5.shutdown()
        return True
        
    except ImportError:
        logger.error("✗ MetaTrader5 module not installed")
        logger.info("\nInstall it with: pip install MetaTrader5")
        return False
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


def test_mt5_symbols():
    """Test available symbols in MT5"""
    logger.info("\n" + "="*80)
    logger.info("TESTING MT5 SYMBOLS")
    logger.info("="*80)
    
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            logger.error("✗ Failed to initialize MT5")
            return False
        
        # Get all symbols
        symbols = mt5.symbols_get()
        if symbols is None or len(symbols) == 0:
            logger.error("✗ No symbols available")
            mt5.shutdown()
            return False
        
        logger.info(f"✓ Found {len(symbols)} symbols")
        
        # Look for our target symbols
        target_keywords = ['BTC', 'US30', 'XAU', 'GOLD']
        
        logger.info("\nSearching for target symbols:")
        for keyword in target_keywords:
            matching = [s.name for s in symbols if keyword in s.name.upper()]
            if matching:
                logger.info(f"\n  {keyword} symbols:")
                for sym in matching[:5]:  # Show first 5
                    logger.info(f"    - {sym}")
            else:
                logger.info(f"\n  {keyword}: Not found")
        
        mt5.shutdown()
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


def test_mt5_data_client_with_login():
    """Test our MT5 data client with login"""
    logger.info("\n" + "="*80)
    logger.info("TESTING MT5 DATA CLIENT WITH LOGIN")
    logger.info("="*80)
    
    try:
        from src.mt5_data_client import MT5DataClient
        
        # Try HFM account first
        broker = 'hfm'
        account_info = MT5_ACCOUNTS[broker]
        
        logger.info(f"\nUsing {broker.upper()} account:")
        logger.info(f"  Account: {account_info['account']}")
        logger.info(f"  Server: {account_info['server']}")
        
        # Test with common symbol names
        test_symbols = ['XAUUSD', 'US30', 'BTCUSD']
        
        for symbol in test_symbols:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing {symbol}")
            logger.info(f"{'='*80}")
            
            client = MT5DataClient(
                symbol=symbol,
                timeframes=['5m'],
                buffer_size=100,
                account=account_info['account'],
                password=account_info['password'],
                server=account_info['server']
            )
            
            if not client.connect():
                logger.warning(f"⚠ Could not connect for {symbol}")
                continue
            
            # Fetch data
            data = client.get_latest_candles('5m', count=10)
            
            if data.empty:
                logger.warning(f"⚠ No data for {symbol}")
                client.disconnect()
                continue
            
            logger.info(f"✓ Received {len(data)} candles")
            
            # Show latest
            latest = data.iloc[-1]
            logger.info(f"\nLatest candle:")
            logger.info(f"  Time: {latest['timestamp']}")
            logger.info(f"  Close: ${latest['close']:.2f}")
            logger.info(f"  Volume: {latest['volume']:.0f}")
            
            # Check freshness
            now = datetime.now()
            latest_time = latest['timestamp']
            if hasattr(latest_time, 'to_pydatetime'):
                latest_time = latest_time.to_pydatetime()
            
            age_seconds = (now - latest_time).total_seconds()
            logger.info(f"  Age: {age_seconds:.0f} seconds ({age_seconds/60:.1f} minutes)")
            
            if age_seconds < 300:  # 5 minutes
                logger.info(f"  ✅ REAL-TIME DATA!")
            else:
                logger.warning(f"  ⚠ Data is {age_seconds/60:.1f} minutes old")
            
            client.disconnect()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error: {e}", exc_info=True)
        return False


def main():
    """Run all MT5 tests"""
    logger.info("="*80)
    logger.info("MT5 CONNECTION TEST")
    logger.info("="*80)
    logger.info(f"Current time: {datetime.now()}")
    logger.info("")
    
    # Test 1: Basic connection
    basic_ok = test_mt5_basic()
    
    if not basic_ok:
        logger.info("\n" + "="*80)
        logger.info("SETUP REQUIRED")
        logger.info("="*80)
        logger.info("\n1. Install MetaTrader5:")
        logger.info("   pip install MetaTrader5")
        logger.info("\n2. Make sure MT5 terminal is running and logged in")
        logger.info("\n3. Run this test again")
        return
    
    # Test 2: Check symbols
    test_mt5_symbols()
    
    # Test 3: Test data client with login
    test_mt5_data_client_with_login()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("NEXT STEPS")
    logger.info("="*80)
    logger.info("\n1. Make sure MT5 terminal is running and logged in")
    logger.info("2. Note which symbols are available (XAUUSD, US30, BTCUSD, etc.)")
    logger.info("3. Update config.json with MT5 settings")
    logger.info("4. Your scanner will get REAL-TIME data from your broker!")
    logger.info("\n" + "="*80)


if __name__ == "__main__":
    main()
