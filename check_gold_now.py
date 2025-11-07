"""Check current Gold market conditions to verify signal quality."""
import yfinance as yf
import pandas as pd
from datetime import datetime
from src.indicator_calculator import IndicatorCalculator

print("=" * 80)
print("CHECKING CURRENT GOLD MARKET CONDITIONS")
print("=" * 80)

# Fetch Gold Futures data (what scanner uses)
print("\n📊 Fetching Gold Futures (GC=F) data...")
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

# Reset index
data = data.reset_index()
data = data.rename(columns={'Datetime': 'timestamp'})

print(f"✅ Fetched {len(data)} candles")

# Calculate indicators
calc = IndicatorCalculator()

# EMAs
data['ema_9'] = calc.calculate_ema(data, 9)
data['ema_21'] = calc.calculate_ema(data, 21)
data['ema_50'] = calc.calculate_ema(data, 50)

# VWAP
data['vwap'] = calc.calculate_vwap(data)

# RSI
data['rsi'] = calc.calculate_rsi(data, 14)
data['rsi_7'] = calc.calculate_rsi(data, 7)

# ADX
data['adx'] = calc.calculate_adx(data, 14)

# ATR
data['atr'] = calc.calculate_atr(data, 14)

# Volume MA
data['volume_ma'] = calc.calculate_volume_ma(data, 20)

# Get last few candles
last = data.iloc[-1]
prev = data.iloc[-2]
prev2 = data.iloc[-3]

print("\n" + "=" * 80)
print("CURRENT MARKET CONDITIONS (5m timeframe)")
print("=" * 80)

print(f"\n💰 PRICE:")
print(f"   Current: ${last['close']:,.2f}")
print(f"   Previous: ${prev['close']:,.2f}")
print(f"   Change: ${last['close'] - prev['close']:+.2f}")

print(f"\n📈 TREND INDICATORS:")
print(f"   EMA(9):  ${last['ema_9']:,.2f}")
print(f"   EMA(21): ${last['ema_21']:,.2f}")
print(f"   EMA(50): ${last['ema_50']:,.2f}")
print(f"   VWAP:    ${last['vwap']:,.2f}")

# Determine trend
if last['close'] > last['ema_50']:
    trend = "UPTREND ✅"
    trend_strength = "Strong" if last['ema_9'] > last['ema_21'] > last['ema_50'] else "Weak"
else:
    trend = "DOWNTREND ⚠️"
    trend_strength = "Strong" if last['ema_9'] < last['ema_21'] < last['ema_50'] else "Weak"

print(f"\n🎯 TREND ANALYSIS:")
print(f"   Direction: {trend}")
print(f"   Strength: {trend_strength}")
print(f"   Price vs EMA(50): ${last['close'] - last['ema_50']:+.2f}")

print(f"\n⚡ MOMENTUM:")
print(f"   RSI(14): {last['rsi']:.1f}")
print(f"   RSI(7):  {last['rsi_7']:.1f}")
print(f"   ADX:     {last['adx']:.1f}")

# Check RSI trend
rsi_7_trend = "Rising" if last['rsi_7'] > prev['rsi_7'] > prev2['rsi_7'] else \
              "Falling" if last['rsi_7'] < prev['rsi_7'] < prev2['rsi_7'] else "Flat"
print(f"   RSI(7) Trend: {rsi_7_trend}")
print(f"   RSI(7) Values: {prev2['rsi_7']:.1f} -> {prev['rsi_7']:.1f} -> {last['rsi_7']:.1f}")

print(f"\n📊 VOLUME:")
volume_ratio = last['volume'] / last['volume_ma']
print(f"   Current: {last['volume']:,.0f}")
print(f"   Average: {last['volume_ma']:,.0f}")
print(f"   Ratio: {volume_ratio:.2f}x")

print(f"\n💥 VOLATILITY:")
print(f"   ATR: ${last['atr']:.2f}")

# Check last 10 candles trend
if len(data) >= 10:
    price_10_ago = data['close'].iloc[-10]
    price_change = last['close'] - price_10_ago
    price_change_pct = (price_change / price_10_ago) * 100
    
    print(f"\n📉 RECENT PRICE ACTION (Last 10 candles):")
    print(f"   10 candles ago: ${price_10_ago:,.2f}")
    print(f"   Current: ${last['close']:,.2f}")
    print(f"   Change: ${price_change:+.2f} ({price_change_pct:+.2f}%)")
    
    if price_change > 0:
        print(f"   Direction: RISING ⬆️")
    else:
        print(f"   Direction: FALLING ⬇️")

print("\n" + "=" * 80)
print("SIGNAL VALIDATION")
print("=" * 80)

# Check if momentum shift LONG would be valid
print("\n🟢 LONG Signal Validation:")
checks = []

# Check 1: Price above EMA(50)
if last['close'] > last['ema_50']:
    checks.append("✅ Price above EMA(50) - Uptrend confirmed")
else:
    checks.append(f"❌ Price below EMA(50) by ${last['ema_50'] - last['close']:.2f} - DOWNTREND!")

# Check 2: RSI turning up
if last['rsi_7'] > prev['rsi_7'] > prev2['rsi_7']:
    checks.append("✅ RSI(7) turning up")
else:
    checks.append("❌ RSI(7) not turning up consistently")

# Check 3: ADX
if last['adx'] >= 18:
    checks.append(f"✅ ADX {last['adx']:.1f} >= 18 - Trend present")
else:
    checks.append(f"❌ ADX {last['adx']:.1f} < 18 - Weak trend")

# Check 4: Volume
if volume_ratio >= 1.2:
    checks.append(f"✅ Volume {volume_ratio:.2f}x >= 1.2x")
else:
    checks.append(f"❌ Volume {volume_ratio:.2f}x < 1.2x")

# Check 5: Recent price action
if len(data) >= 10:
    if last['close'] > price_10_ago:
        checks.append("✅ Price rising over last 10 candles")
    else:
        checks.append(f"❌ Price falling over last 10 candles ({price_change:+.2f})")

for check in checks:
    print(f"   {check}")

# Overall verdict
passed = sum(1 for c in checks if c.startswith("✅"))
total = len(checks)

print(f"\n📊 VERDICT: {passed}/{total} checks passed")

if passed == total:
    print("   ✅ LONG signal would be VALID")
elif passed >= 3:
    print("   ⚠️ LONG signal QUESTIONABLE - some conditions not met")
else:
    print("   ❌ LONG signal INVALID - trend not confirmed!")

print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if last['close'] > last['ema_50']:
    print("✅ Market is in UPTREND - LONG signals are appropriate")
else:
    print("⚠️ Market is in DOWNTREND - LONG signals should be REJECTED")
    print("   Only SHORT signals should be considered in this market condition")

print("\n" + "=" * 80)
