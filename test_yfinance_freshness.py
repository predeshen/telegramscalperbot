"""
Test yfinance actual data freshness RIGHT NOW
"""
import yfinance as yf
from datetime import datetime, timezone
import pandas as pd

print("="*80)
print("YFINANCE DATA FRESHNESS TEST")
print("="*80)

now_utc = datetime.now(timezone.utc)
print(f"Current UTC time: {now_utc}")
print("")

symbols = [
    ('BTC-USD', 'Bitcoin'),
    ('^DJI', 'US30 (Dow Jones)'),
    ('GC=F', 'Gold Futures (XAU/USD)')
]

results = {}

for ticker, name in symbols:
    print(f"{'='*80}")
    print(f"Testing {name} ({ticker})")
    print(f"{'='*80}")
    
    try:
        # Fetch 1-minute data
        data = yf.Ticker(ticker)
        hist = data.history(period='1d', interval='1m')
        
        if hist.empty:
            print(f"✗ No data received")
            results[name] = None
            continue
        
        # Get latest candle
        latest_time = hist.index[-1]
        latest_price = hist.iloc[-1]['Close']
        
        # Calculate age
        if latest_time.tzinfo is None:
            latest_time_utc = latest_time.replace(tzinfo=timezone.utc)
        else:
            latest_time_utc = latest_time.astimezone(timezone.utc)
        
        age_seconds = (now_utc - latest_time_utc).total_seconds()
        age_minutes = age_seconds / 60
        
        print(f"Latest candle: {latest_time_utc}")
        print(f"Price: ${latest_price:.2f}")
        print(f"Age: {age_seconds:.0f} seconds ({age_minutes:.1f} minutes)")
        
        if age_minutes < 5:
            print("✅ REAL-TIME (< 5 min)")
            results[name] = 'real-time'
        elif age_minutes < 15:
            print("✓ FRESH (< 15 min)")
            results[name] = 'fresh'
        elif age_minutes < 60:
            print("⚠ ACCEPTABLE (< 1 hour)")
            results[name] = 'acceptable'
        else:
            print(f"❌ STALE ({age_minutes:.0f} min old)")
            results[name] = 'stale'
        
        print("")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        results[name] = 'error'
        print("")

print("="*80)
print("SUMMARY")
print("="*80)

for name, status in results.items():
    if status == 'real-time':
        print(f"{name}: ✅ REAL-TIME")
    elif status == 'fresh':
        print(f"{name}: ✓ FRESH")
    elif status == 'acceptable':
        print(f"{name}: ⚠ ACCEPTABLE")
    elif status == 'stale':
        print(f"{name}: ❌ STALE")
    else:
        print(f"{name}: ✗ ERROR")

print("")
print("="*80)
print("RECOMMENDATION")
print("="*80)

if all(s in ['real-time', 'fresh'] for s in results.values()):
    print("\n✅ yfinance is providing real-time/fresh data for all assets!")
    print("✅ Safe to use as primary provider")
    print("\nAdvantages:")
    print("  - No API keys needed")
    print("  - No rate limits")
    print("  - All assets supported")
    print("  - Simple and reliable")
else:
    print("\n⚠️ yfinance has delays for some assets")
    print("\nBetter strategy:")
    print("  - Kraken for BTC (real-time, no limits)")
    print("  - Alpha Vantage for US30/XAU (better quality)")
    print("  - yfinance as fallback")

print("="*80)
