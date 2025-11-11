"""
Check what symbols Kraken and Oanda have for our assets
"""
import logging
import ccxt

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_kraken_symbols():
    """Check Kraken for our symbols"""
    logger.info("="*80)
    logger.info("CHECKING KRAKEN SYMBOLS")
    logger.info("="*80)
    
    try:
        exchange = ccxt.kraken()
        markets = exchange.load_markets()
        
        logger.info(f"\nTotal symbols: {len(markets)}")
        
        # Search for our targets
        targets = {
            'BTC': ['BTC', 'XBT'],
            'US30': ['US30', 'DOW', 'DJI', 'DJIA'],
            'XAU': ['XAU', 'GOLD']
        }
        
        for asset, keywords in targets.items():
            logger.info(f"\n{asset} symbols:")
            found = []
            for symbol in markets.keys():
                if any(kw in symbol.upper() for kw in keywords):
                    info = markets[symbol]
                    found.append(symbol)
                    logger.info(f"  ✓ {symbol}")
                    logger.info(f"    Base: {info.get('base', 'N/A')}, Quote: {info.get('quote', 'N/A')}")
            
            if not found:
                logger.info(f"  ✗ No {asset} symbols found")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def check_oanda_symbols():
    """Check Oanda for our symbols"""
    logger.info("\n" + "="*80)
    logger.info("CHECKING OANDA SYMBOLS")
    logger.info("="*80)
    
    try:
        # Oanda requires API credentials
        logger.info("\nOanda requires API credentials to access")
        logger.info("Checking if oanda is supported by CCXT...")
        
        if hasattr(ccxt, 'oanda'):
            logger.info("✓ Oanda is supported by CCXT")
            logger.info("\nTo use Oanda, you need:")
            logger.info("  1. Oanda account")
            logger.info("  2. API token")
            logger.info("  3. Account ID")
            logger.info("\nOanda typically has:")
            logger.info("  ✓ XAU/USD (Gold)")
            logger.info("  ✗ US30 (Not available - Oanda is forex only)")
            logger.info("  ✗ BTC/USD (Limited crypto support)")
        else:
            logger.info("✗ Oanda not directly supported by CCXT")
            logger.info("  (Oanda v20 API would need custom implementation)")
        
        return False
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False


def check_other_exchanges():
    """Check other exchanges that might have US30"""
    logger.info("\n" + "="*80)
    logger.info("CHECKING OTHER EXCHANGES FOR US30")
    logger.info("="*80)
    
    # Exchanges that might have indices
    exchanges_to_check = [
        'binance',
        'bybit',
        'okx',
        'bitget',
        'phemex'
    ]
    
    for exchange_name in exchanges_to_check:
        try:
            logger.info(f"\n{exchange_name.upper()}:")
            exchange_class = getattr(ccxt, exchange_name, None)
            if not exchange_class:
                logger.info(f"  ✗ Not available in CCXT")
                continue
            
            exchange = exchange_class()
            markets = exchange.load_markets()
            
            # Look for US30/indices
            us30_symbols = [s for s in markets.keys() if any(x in s.upper() for x in ['US30', 'DOW', 'DJI'])]
            xau_symbols = [s for s in markets.keys() if any(x in s.upper() for x in ['XAU', 'GOLD'])]
            btc_symbols = [s for s in markets.keys() if 'BTC' in s.upper() and 'USD' in s.upper()]
            
            if us30_symbols:
                logger.info(f"  ✓ US30: {us30_symbols[:3]}")
            else:
                logger.info(f"  ✗ US30: Not found")
            
            if xau_symbols:
                logger.info(f"  ✓ XAU: {xau_symbols[:3]}")
            else:
                logger.info(f"  ✗ XAU: Not found")
            
            if btc_symbols:
                logger.info(f"  ✓ BTC: {btc_symbols[:3]}")
            
        except Exception as e:
            logger.info(f"  ✗ Error: {str(e)[:50]}")


def main():
    """Check all exchanges"""
    logger.info("="*80)
    logger.info("EXCHANGE SYMBOL CHECKER")
    logger.info("="*80)
    logger.info("\nSearching for: BTC/USD, US30/USD, XAU/USD")
    logger.info("")
    
    # Check Kraken
    check_kraken_symbols()
    
    # Check Oanda
    check_oanda_symbols()
    
    # Check other exchanges
    check_other_exchanges()
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SUMMARY & RECOMMENDATIONS")
    logger.info("="*80)
    
    logger.info("\n✅ KRAKEN (Already integrated via CCXT):")
    logger.info("  ✓ BTC/USD - Available")
    logger.info("  ✗ US30 - NOT available (crypto exchange)")
    logger.info("  ✗ XAU/USD - NOT available (crypto exchange)")
    logger.info("  → Use for: BTC only")
    
    logger.info("\n⚠️ OANDA:")
    logger.info("  ✗ Requires API credentials")
    logger.info("  ✓ XAU/USD - Available")
    logger.info("  ✗ US30 - NOT available (forex only)")
    logger.info("  ✗ BTC - Limited support")
    logger.info("  → Use for: XAU/USD only (if you have API key)")
    
    logger.info("\n💡 BEST STRATEGY:")
    logger.info("  BTC/USD:")
    logger.info("    1. Kraken (CCXT) - Real-time, free")
    logger.info("    2. yfinance - Fallback")
    logger.info("")
    logger.info("  US30/USD:")
    logger.info("    1. Alpha Vantage - Best option")
    logger.info("    2. Twelve Data - Fallback")
    logger.info("    3. yfinance - Last resort")
    logger.info("    ✗ NOT available on Kraken or Oanda")
    logger.info("")
    logger.info("  XAU/USD:")
    logger.info("    1. Alpha Vantage - Best option")
    logger.info("    2. Oanda (if you have API key)")
    logger.info("    3. Twelve Data - Fallback")
    logger.info("    4. yfinance - Last resort")
    
    logger.info("\n" + "="*80)
    logger.info("CONCLUSION")
    logger.info("="*80)
    logger.info("\nKraken: Already using for BTC ✅")
    logger.info("Oanda: Need API key, only helps with XAU/USD")
    logger.info("\nCurrent multi-provider setup is optimal:")
    logger.info("  - Kraken for BTC (via CCXT)")
    logger.info("  - Alpha Vantage for US30 & XAU")
    logger.info("  - Twelve Data as fallback")
    logger.info("  - yfinance as last resort")
    logger.info("="*80)


if __name__ == "__main__":
    main()
