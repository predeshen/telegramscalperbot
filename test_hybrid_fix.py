"""Test the hybrid client fix"""
import sys
import logging
from src.config_loader import ConfigLoader
from src.hybrid_data_client import HybridDataClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_config_load():
    """Test that config loads with data_providers"""
    try:
        config = ConfigLoader.load("config/config.json")
        logger.info(f"✓ Config loaded successfully")
        logger.info(f"  Exchange: {config.exchange.name}")
        logger.info(f"  Symbol: {config.exchange.symbol}")
        
        if hasattr(config, 'data_providers') and config.data_providers:
            logger.info(f"  Data providers configured:")
            logger.info(f"    - Alpha Vantage: {'Yes' if config.data_providers.alpha_vantage_key else 'No'}")
            logger.info(f"    - Twelve Data: {'Yes' if config.data_providers.twelve_data_key else 'No'}")
            logger.info(f"    - Preferred: {config.data_providers.preferred_provider or 'Auto'}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Config load failed: {e}")
        return False

def test_hybrid_client():
    """Test that hybrid client can be initialized"""
    try:
        config = ConfigLoader.load("config/config.json")
        
        if config.exchange.name != 'hybrid':
            logger.warning(f"Exchange is '{config.exchange.name}', not 'hybrid'. Skipping hybrid client test.")
            return True
        
        # Get data provider keys
        alpha_vantage_key = None
        twelve_data_key = None
        preferred_provider = None
        
        if hasattr(config, 'data_providers') and config.data_providers:
            alpha_vantage_key = config.data_providers.alpha_vantage_key
            twelve_data_key = config.data_providers.twelve_data_key
            preferred_provider = config.data_providers.preferred_provider
        
        # Initialize hybrid client
        client = HybridDataClient(
            symbol=config.exchange.symbol,
            timeframes=config.exchange.timeframes,
            buffer_size=100,
            alpha_vantage_key=alpha_vantage_key,
            twelve_data_key=twelve_data_key,
            preferred_provider=preferred_provider
        )
        
        logger.info(f"✓ HybridDataClient initialized")
        
        # Get client info
        info = client.get_client_info()
        logger.info(f"  Client type: {info['client_type']}")
        logger.info(f"  Asset type: {info['asset_type']}")
        logger.info(f"  Providers tried: {', '.join(info['providers_tried'])}")
        
        # Test connection
        if client.connect():
            logger.info(f"✓ Connected successfully")
            
            # Try to fetch some data
            df = client.get_latest_candles(config.exchange.timeframes[0], 10)
            if not df.empty:
                logger.info(f"✓ Fetched {len(df)} candles")
                logger.info(f"  Latest price: ${df.iloc[-1]['close']:.2f}")
                return True
            else:
                logger.error(f"✗ No data returned")
                return False
        else:
            logger.error(f"✗ Connection failed")
            return False
            
    except Exception as e:
        logger.error(f"✗ Hybrid client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Testing Hybrid Client Fix")
    logger.info("=" * 60)
    
    success = True
    
    logger.info("\n1. Testing config load...")
    if not test_config_load():
        success = False
    
    logger.info("\n2. Testing hybrid client...")
    if not test_hybrid_client():
        success = False
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("✓ All tests passed!")
        sys.exit(0)
    else:
        logger.error("✗ Some tests failed")
        sys.exit(1)
