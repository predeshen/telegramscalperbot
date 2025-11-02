#!/usr/bin/env python3
"""Check which exchanges support XAU/USD spot gold trading."""
import ccxt

print("Checking exchanges for XAU/USD spot gold support...\n")

# List of popular exchanges that might support gold
exchanges_to_check = [
    'binance',
    'bybit', 
    'okx',
    'bitfinex',
    'huobi',
    'gateio',
    'kucoin',
    'mexc',
    'bitget',
    'phemex'
]

supported = []
not_supported = []

for exchange_name in exchanges_to_check:
    if exchange_name not in ccxt.exchanges:
        continue
    
    try:
        exchange = getattr(ccxt, exchange_name)()
        markets = exchange.load_markets()
        
        # Check for XAU/USD or similar gold symbols
        gold_symbols = [s for s in markets.keys() if 'XAU' in s and 'USD' in s and 'XAUT' not in s]
        
        if gold_symbols:
            supported.append((exchange_name, gold_symbols))
            print(f"✅ {exchange_name}: {', '.join(gold_symbols)}")
        else:
            not_supported.append(exchange_name)
            print(f"❌ {exchange_name}: No XAU/USD")
    
    except Exception as e:
        print(f"⚠️ {exchange_name}: Error - {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if supported:
    print(f"\n✅ Exchanges with XAU/USD support ({len(supported)}):")
    for ex, symbols in supported:
        print(f"   • {ex}: {', '.join(symbols)}")
else:
    print("\n❌ No exchanges found with XAU/USD spot gold")
    print("\nNote: XAU/USD is typically traded on:")
    print("   • Forex brokers (MT4/MT5)")
    print("   • CFD platforms")
    print("   • Not commonly on crypto exchanges")
    print("\nFor crypto exchanges, consider:")
    print("   • PAXG/USD (Paxos Gold)")
    print("   • XAUT/USD (Tether Gold)")
    print("   • These are tokenized gold, not spot XAU/USD")

print("\n" + "=" * 60)
