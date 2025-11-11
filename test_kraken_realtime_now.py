"""
Check if Kraken is actually giving us real-time data RIGHT NOW
"""
import ccxt
import pandas as pd
from datetime import datetime

print("="*80)
print("KRAKEN REAL-TIME DATA CHECK")
print("="*80)
print(f"Current time: {datetime.now()}")
print("")

# Test Kraken directly
exchange = ccxt.kraken()

print("Fetching BTC/USD 1-minute candles from Kraken...")
ohlcv = exchange.fetch_ohlcv('BTC/USD', '1m', limit=5)

df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

print(f"\nReceived {len(df)} candles:")
print(df.to_string())

# Check freshness
now = datetime.now()
latest_time = df.iloc[-1]['timestamp'].to_pydatetime()
age_seconds = (now - latest_time).total_seconds()

print(f"\n{'='*80}")
print("FRESHNESS CHECK")
print(f"{'='*80}")
print(f"Current time:  {now}")
print(f"Latest candle: {latest_time}")
print(f"Age: {age_seconds:.0f} seconds ({age_seconds/60:.1f} minutes)")

if age_seconds < 120:  # 2 minutes
    print("✅ DATA IS REAL-TIME!")
else:
    print(f"❌ DATA IS STALE ({age_seconds/60:.1f} minutes old)")
    print("\nThis suggests:")
    print("1. Kraken's BTC/USD pair has low liquidity")
    print("2. Try BTC/USDT instead")
    print("3. Or the market you're trading is different from Kraken")

# Test BTC/USDT
print(f"\n{'='*80}")
print("Testing BTC/USDT...")
print(f"{'='*80}")

ohlcv2 = exchange.fetch_ohlcv('BTC/USDT', '1m', limit=5)
df2 = pd.DataFrame(ohlcv2, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df2['timestamp'] = pd.to_datetime(df2['timestamp'], unit='ms')

latest_time2 = df2.iloc[-1]['timestamp'].to_pydatetime()
age_seconds2 = (now - latest_time2).total_seconds()

print(f"Latest candle: {latest_time2}")
print(f"Age: {age_seconds2:.0f} seconds ({age_seconds2/60:.1f} minutes)")

if age_seconds2 < 120:
    print("✅ BTC/USDT IS REAL-TIME!")
else:
    print(f"❌ BTC/USDT IS ALSO STALE")

print(f"\n{'='*80}")
print("QUESTION FOR YOU")
print(f"{'='*80}")
print("\nWhich broker/platform are you actively trading on RIGHT NOW?")
print("  - MT5 (Vantage/HFM)?")
print("  - Different broker?")
print("  - Different exchange?")
print("\nThe data source needs to match your trading platform!")
print("="*80)
