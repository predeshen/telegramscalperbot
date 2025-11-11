"""
Check timezone and actual data freshness
"""
from datetime import datetime, timezone
import ccxt
import pandas as pd

print("="*80)
print("TIMEZONE & DATA FRESHNESS CHECK")
print("="*80)

# Get current time in different formats
now_local = datetime.now()
now_utc = datetime.now(timezone.utc)

print(f"\nLocal time (system): {now_local}")
print(f"UTC time (actual):   {now_utc}")
print(f"Timezone offset:     {now_local.astimezone().strftime('%z')}")

# Fetch Kraken data
print(f"\n{'='*80}")
print("Fetching Kraken BTC/USD data...")
print(f"{'='*80}")

exchange = ccxt.kraken()
ohlcv = exchange.fetch_ohlcv('BTC/USD', '1m', limit=3)

df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)

print("\nLatest 3 candles:")
for idx, row in df.iterrows():
    print(f"  {row['timestamp']} - Close: ${row['close']:.2f}")

# Calculate age using UTC
latest_time_utc = df.iloc[-1]['timestamp']
age_seconds = (now_utc - latest_time_utc).total_seconds()
age_minutes = age_seconds / 60

print(f"\n{'='*80}")
print("FRESHNESS ANALYSIS")
print(f"{'='*80}")
print(f"Current UTC time:    {now_utc}")
print(f"Latest candle (UTC): {latest_time_utc}")
print(f"Age: {age_seconds:.0f} seconds ({age_minutes:.1f} minutes)")

if age_minutes < 5:
    print("✅ DATA IS REAL-TIME (< 5 minutes)")
elif age_minutes < 15:
    print("✓ DATA IS FRESH (< 15 minutes)")
elif age_minutes < 60:
    print("⚠ DATA IS ACCEPTABLE (< 1 hour)")
else:
    print(f"❌ DATA IS STALE (> 1 hour)")

print(f"\n{'='*80}")
print("EXPLANATION")
print(f"{'='*80}")

if age_minutes > 60:
    print("\nThe data is genuinely stale. This could mean:")
    print("1. BTC markets are in a low-volume period")
    print("2. Kraken's BTC/USD pair has low activity")
    print("3. You're trading on a different platform (MT5?)")
    print("\nFor real-time data matching your trading platform:")
    print("  → Use MT5 data client if trading on MT5")
    print("  → Or use Alpha Vantage/Twelve Data (5-15 min delay)")
else:
    print("\n✅ The data is actually fresh!")
    print("The previous test had timezone confusion.")
    print("Kraken data is working correctly.")

print("="*80)
