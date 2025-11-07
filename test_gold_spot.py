"""Test Gold spot price sources."""
import yfinance as yf
import pandas as pd

print("=" * 80)
print("TESTING GOLD SPOT PRICE SOURCES")
print("=" * 80)

print(f"\nYour broker shows: $4,005.00")
print(f"Scanner showed: $4,010.10 (GC=F futures)\n")

# Test different tickers
tickers_to_test = [
    ('GC=F', 'Gold Futures'),
    ('GOLD', 'Gold Spot (if available)'),
]

for ticker, name in tickers_to_test:
    try:
        print(f"\n📊 Testing {ticker} ({name})...")
        gold = yf.Ticker(ticker)
        
        # Get recent data
        hist = gold.history(period='1d', interval='5m')
        
        if not hist.empty:
            latest = hist['Close'].iloc[-1]
            print(f"   ✅ Latest price: ${latest:.2f}")
            diff = latest - 4005.00
            print(f"   Difference from broker: ${diff:+.2f}")
        else:
            print(f"   ❌ No data available")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")

print("\n" + "=" * 80)
print("ALTERNATIVE SOLUTION: Use a price offset")
print("=" * 80)
print("""
Since Yahoo Finance spot prices aren't reliable, we have 2 options:

OPTION 1: Add a price offset to the scanner
- Keep using GC=F (reliable data)
- Subtract $5 from all prices in alerts
- Simple configuration change

OPTION 2: Use a different data provider
- Alpha Vantage (free tier: 25 calls/day)
- Twelve Data (free tier: 800 calls/day)
- Requires API key but gives real spot prices

RECOMMENDED: Option 1 (price offset)
- Easiest to implement
- No new dependencies
- Keeps reliable Yahoo Finance data
- Just adjusts the displayed prices
""")
print("=" * 80)
