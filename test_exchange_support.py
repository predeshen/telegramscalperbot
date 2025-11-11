"""
Test which exchanges support our target symbols
"""
import logging
import ccxt

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_exchange_for_symbols(exchange_name, target_symbols):
    """Check if an exchange supports our target symbols"""
    try:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Checking {exchange_name.upper()}")
        logger.info(f"{'='*80}")
        
        markets = exchange.load_markets()
        
        found = {}
        for symbol in target_symbols:
            # Try exact match
            if symbol in markets:
                found[symbol] = True
                logger.info(f"  ✓ {symbol}")
            else:
                # Try to find similar
                similar = [s for s in markets.keys() if 
                          any(part in s for part in symbol.replace('/', '').split('/'))]
                if similar:
                    logger.info(f"  ~ {symbol} not found, but similar: {similar[:3]}")
                else:
                    logger.info(f"  ✗ {symbol}")
        
        return found
        
    except Exception as e:
        logger.error(f"  Error checking {exchange_name}: {e}")
        return {}


def main():
    """Check multiple exchanges for our symbols"""
    
    target_symbols = [
        'BTC/USD',
        'BTC/USDT',
        'XAU/USD',
        'XAUUSD',
        'US30/USD',
        'US30USD',
    ]
    
    # Exchanges that commonly support forex and indices
    exchanges_to_check = [
        'kraken',      # Crypto exchange (current)
        'binance',     # Largest crypto exchange
        'oanda',       # Forex broker (supports indices)
        'fxcm',        # Forex broker
        'alpaca',      # Stock/crypto broker
    ]
    
    logger.info("="*80)
    logger.info("EXCHANGE SYMBOL SUPPORT CHECK")
    logger.info("="*80)
    logger.info(f"\nTarget symbols: {', '.join(target_symbols)}")
    
    results = {}
    for exchange_name in exchanges_to_check:
        try:
            results[exchange_name] = check_exchange_for_symbols(exchange_name, target_symbols)
        except Exception as e:
            logger.error(f"\nCould not check {exchange_name}: {e}")
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY")
    logger.info(f"{'='*80}")
    
    for symbol in target_symbols:
        supporting_exchanges = [ex for ex, found in results.items() if symbol in found]
        if supporting_exchanges:
            logger.info(f"{symbol}: {', '.join(supporting_exchanges)}")
        else:
            logger.info(f"{symbol}: ❌ NOT FOUND on any exchange")
    
    logger.info(f"\n{'='*80}")
    logger.info("RECOMMENDATIONS")
    logger.info(f"{'='*80}")
    logger.info("• BTC/USD: Use Kraken or Binance (both work)")
    logger.info("• XAU/USD: Need a FOREX broker like OANDA or FXCM")
    logger.info("• US30/USD: Need a FOREX/CFD broker like OANDA or FXCM")
    logger.info("\nKraken is a CRYPTO exchange - it doesn't support traditional forex or indices!")
    logger.info("You need to configure additional exchanges for XAU/USD and US30/USD")


if __name__ == "__main__":
    main()
