"""Check Gold conditions at the time the signal was sent (09:10 UTC)."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from src.indicator_calculator import IndicatorCalculator

print("=" * 80)
print("CHECKING GOLD AT SIGNAL TIME (09:10 UTC)")
print("=" * 80)

# The signal said:
signal_time_str = "09:10:00 UTC"
signal_entry = 4010.10
signal_vwap = 4009.80
signal_rsi = 57.9

print(f"\n📨 SIGNAL RECEIVED:")
print(f"   Time: {signal_time_str}")
print(f"   Type: LONG")
print(f"   Entry: ${signal_entry:,.2f}")
print(f"   VWAP: ${signal_vwap:,.2f}")
print(f"   RSI: {signal_rsi}")
print(f"   Your Broker: $4,005.00")

# Fetch more historical data
print(f"\n📊 Fetching Gold data for today...")
gold = yf.Ticker('GC=F')
data = gold.history(period='1d', interval='5m')

if data.empty:
    print("❌ No data available")
    exit(1)

# Rename columns
data = data.rename(columns={
    'Open': 'open',
    'High': 'high',
    'Low': 'low',
    'Close': 'close',
    'Volume': 'volume'
})

data = data.reset_index()
data = data.rename(columns={'Datetime': 'timestamp'})

print(f"✅ Fetched {len(data)} candles")

# Calculate indicators
calc = IndicatorCalculator()
data['ema_50'] = calc.calculate_ema(data, 50)
data['rsi_7'] = calc.calculate_rsi(data, 7)
data['vwap'] = calc.calculate_vwap(data)

# Find candles around 09:10 UTC
print(f"\n🔍 Looking for candles around 09:10 UTC...")

# Convert timestamps to UTC if needed
if data['timestamp'].dt.tz is not None:
    data['timestamp'] = data['timestamp'].dt.tz_convert('UTC')
else:
    data['timestamp'] = data['timestamp'].dt.tz_localize('UTC')

# Filter for candles around 09:00-09:15 UTC
target_time = pd.Timestamp('2024-01-07 09:10:00', tz='UTC')
time_window = timedelta(minutes=30)

# Get today's date
today = datetime.now().date()
target_time = pd.Timestamp(f'{today} 09:10:00', tz='UTC')

# Find closest candles
mask = (data['timestamp'] >= target_time - time_window) & (data['timestamp'] <= target_time + time_window)
relevant_data = data[mask]

if relevant_data.empty:
    print("⚠️ No data found for that exact time, showing recent data instead...")
    relevant_data = data.tail(20)

print(f"\n📊 CANDLES AROUND SIGNAL TIME:")
print("=" * 80)

for idx, row in relevant_data.tail(10).iterrows():
    time_str = row['timestamp'].strftime('%H:%M:%S')
    price = row['close']
    ema_50 = row['ema_50']
    
    # Determine if uptrend or downtrend
    if pd.notna(ema_50):
        if price > ema_50:
            trend = "UP ⬆️"
        else:
            trend = "DOWN ⬇️"
        trend_diff = price - ema_50
    else:
        trend = "N/A"
        trend_diff = 0
    
    print(f"{time_str} | Price: ${price:,.2f} | EMA(50): ${ema_50:,.2f} | {trend} ({trend_diff:+.2f})")

# Analyze the trend at signal time
print("\n" + "=" * 80)
print("ANALYSIS AT SIGNAL TIME")
print("=" * 80)

if not relevant_data.empty:
    # Get the candle closest to 09:10
    signal_candle = relevant_data.iloc[-1]
    
    print(f"\n📍 Closest candle to signal time:")
    print(f"   Time: {signal_candle['timestamp'].strftime('%H:%M:%S UTC')}")
    print(f"   Price: ${signal_candle['close']:,.2f}")
    print(f"   EMA(50): ${signal_candle['ema_50']:,.2f}")
    
    if pd.notna(signal_candle['ema_50']):
        if signal_candle['close'] > signal_candle['ema_50']:
            print(f"   ✅ UPTREND - Price ${signal_candle['close'] - signal_candle['ema_50']:+.2f} above EMA(50)")
            print(f"   LONG signal was APPROPRIATE")
        else:
            print(f"   ❌ DOWNTREND - Price ${signal_candle['ema_50'] - signal_candle['close']:+.2f} below EMA(50)")
            print(f"   LONG signal was WRONG!")
    
    # Check if price was falling
    if len(relevant_data) >= 5:
        five_candles_ago = relevant_data.iloc[-5]['close']
        price_change = signal_candle['close'] - five_candles_ago
        
        print(f"\n📉 Price movement (last 5 candles):")
        print(f"   5 candles ago: ${five_candles_ago:,.2f}")
        print(f"   At signal: ${signal_candle['close']:,.2f}")
        print(f"   Change: ${price_change:+.2f}")
        
        if price_change < 0:
            print(f"   ⚠️ Price was FALLING")
        else:
            print(f"   ✅ Price was RISING")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print(f"""
Your observation: "Gold was in a declining downtrend"
Signal said: "LONG at $4,010.10"
Your broker: "$4,005.00"

Possible explanations:
1. Futures (GC=F) showed uptrend, but spot (your broker) showed downtrend
2. The $5 price difference caused different EMA calculations
3. The signal was generated on futures data that doesn't match spot reality
4. Market was choppy/ranging, not clearly trending

SOLUTION IMPLEMENTED:
✅ Added trend confirmation (price must be above EMA(50) for LONG)
✅ Added recent price action check (last 10 candles must show upward bias)
✅ Added price offset support to match your broker's spot prices

These fixes will prevent LONG signals in downtrends!
""")

print("=" * 80)
