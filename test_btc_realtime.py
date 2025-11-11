"""
Test if BTC data is actually real-time from Kraken
"""
import ccxt
import pandas as pd
from datetime import datetime

print("="*80)
print("TESTING BTC REAL-TIME DATA FROM KRAKEN")
print("="*80)

# Connect to Kraken
exchange = ccxt.kraken()

# Fetch latest 5 candles
print("\nFetching latest 5m candles...")
ohlcv = exchange.fetch_ohlcv('BTC/USD', '5m', limit=5)

# Convert to DataFrame
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

print("\nLatest 5 candles:")
print(df.to_string())

# Check freshness
now = datetime.now()
latest_time = df.iloc[-1]['timestamp'].to_pydatetime().replace(tzinfo=None)
age_seconds = (now - latest_time).total_seconds()
age_minutes = age_seconds / 60

print(f"\n{'='*80}")
print("FRESHNESS CHECK")
print(f"{'='*80}")
print(f"Current time:    {now}")
print(f"Latest candle:   {latest_time}")
print(f"Age:             {age_minutes:.1f} minutes ({age_seconds:.0f} seconds)")

if age_minutes <= 5:
    print(f"✓ Data is REAL-TIME (< 5 minutes old)")
elif age_minutes <= 10:
    print(f"✓ Data is FRESH (< 10 minutes old)")
elif age_minutes <= 30:
    print(f"⚠ Data is STALE ({age_minutes:.1f} minutes old)")
else:
    print(f"✗ Data is VERY STALE ({age_minutes:.1f} minutes old)")

print(f"\n{'='*80}")
print("DIAGNOSIS")
print(f"{'='*80}")

if age_minutes > 10:
    print("⚠ BTC data is stale even though BTC trades 24/7!")
    print("\nPossible causes:")
    print("1. Kraken API issue or maintenance")
    print("2. Network connectivity issue")
    print("3. Your system clock is wrong")
    print("4. Kraken's BTC/USD pair has low liquidity (try BTC/USDT)")
    
    print("\nTesting BTC/USDT instead...")
    ohlcv2 = exchange.fetch_ohlcv('BTC/USDT', '5m', limit=5)
    df2 = pd.DataFrame(ohlcv2, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df2['timestamp'] = pd.to_datetime(df2['timestamp'], unit='ms')
    latest_time2 = df2.iloc[-1]['timestamp'].to_pydatetime().replace(tzinfo=None)
    age_minutes2 = (now - latest_time2).total_seconds() / 60
    
    print(f"\nBTC/USDT latest: {latest_time2}")
    print(f"BTC/USDT age: {age_minutes2:.1f} minutes")
    
    if age_minutes2 < age_minutes:
        print("\n✓ BTC/USDT has fresher data!")
        print("RECOMMENDATION: Use BTC/USDT instead of BTC/USD")
else:
    print("✓ Kraken is providing real-time BTC data")
    print("✓ Your system is working correctly")

print(f"{'='*80}")
