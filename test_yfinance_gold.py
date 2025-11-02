#!/usr/bin/env python3
"""
Test YFinance client with Gold (XAU/USD)
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("TESTING YFINANCE GOLD CLIENT")
print("=" * 80)

# Test 1: Import
print("\n1️⃣ Testing Import...")
try:
    from src.yfinance_client import YFinanceClient
    print("   ✅ Import successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Connection
print("\n2️⃣ Testing Connection...")
try:
    # Try different Gold symbols
    symbols_to_test = [
        ('GC=F', 'Gold Futures'),
        ('XAUUSD=X', 'Gold Spot USD'),
    ]
    
    working_symbol = None
    
    for symbol, name in symbols_to_test:
        print(f"\n   Testing {name} ({symbol})...")
        client = YFinanceClient(
            symbol=symbol,
            timeframes=['15m', '1h', '4h', '1d'],
            buffer_size=200
        )
        
        if client.connect():
            print(f"   ✅ Connected to {name}")
            
            # Try to fetch data
            try:
                df = client.get_latest_candles('1d', count=5)
                if not df.empty:
                    print(f"   ✅ Data available: {len(df)} candles")
                    print(f"   💰 Latest price: ${df.iloc[-1]['close']:,.2f}")
                    working_symbol = (symbol, name)
                    break
                else:
                    print(f"   ⚠️ No data available")
            except Exception as e:
                print(f"   ⚠️ Data fetch error: {e}")
        else:
            print(f"   ❌ Connection failed")
    
    if not working_symbol:
        print("\n   ❌ No working Gold symbol found")
        sys.exit(1)
    
    print(f"\n   ✅ Best symbol: {working_symbol[0]} ({working_symbol[1]})")
    
except Exception as e:
    print(f"   ❌ Connection error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Multi-timeframe data
print("\n3️⃣ Testing Multi-Timeframe Data...")
try:
    client = YFinanceClient(
        symbol=working_symbol[0],
        timeframes=['15m', '1h', '4h', '1d'],
        buffer_size=200
    )
    
    client.connect()
    
    from src.indicator_calculator import IndicatorCalculator
    calc = IndicatorCalculator()
    
    for timeframe in ['15m', '1h', '4h', '1d']:
        try:
            df = client.get_latest_candles(timeframe, count=50)
            
            if not df.empty:
                # Calculate indicators
                df['ema_9'] = calc.calculate_ema(df, 9)
                df['ema_21'] = calc.calculate_ema(df, 21)
                df['ema_50'] = calc.calculate_ema(df, 50)
                df['rsi'] = calc.calculate_rsi(df, 14)
                df['atr'] = calc.calculate_atr(df, 14)
                
                last = df.iloc[-1]
                print(f"   ✅ {timeframe:4s}: ${last['close']:7,.2f} | RSI: {last['rsi']:5.1f} | ATR: ${last['atr']:6.2f}")
            else:
                print(f"   ⚠️ {timeframe}: No data")
        
        except Exception as e:
            print(f"   ⚠️ {timeframe}: {e}")
    
except Exception as e:
    print(f"   ❌ Multi-timeframe error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Current Price
print("\n4️⃣ Testing Current Price...")
try:
    current_price = client.get_current_price()
    if current_price:
        print(f"   ✅ Current Gold price: ${current_price:,.2f}")
    else:
        print(f"   ⚠️ Could not get current price")
except Exception as e:
    print(f"   ⚠️ Current price error: {e}")

print("\n" + "=" * 80)
print("✅ YFINANCE GOLD CLIENT TEST COMPLETE!")
print("=" * 80)
print(f"\n🥇 Recommended symbol for Gold: {working_symbol[0]} ({working_symbol[1]})")
print("\nUpdate your config files with:")
print(f'  "exchange": "yfinance"')
print(f'  "symbol": "{working_symbol[0]}"')
print("=" * 80)
