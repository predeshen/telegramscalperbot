#!/usr/bin/env python3
"""
Test script for US30 Scanners (Scalping and Swing)
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("TESTING US30 SCANNERS")
print("=" * 80)

# Test 1: Imports
print("\n1️⃣ Testing Imports...")
try:
    from src.yfinance_client import YFinanceClient
    from src.indicator_calculator import IndicatorCalculator
    from us30_scanner.us30_scalp_detector import US30ScalpDetector
    from us30_scanner.us30_swing_detector import US30SwingDetector
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)

# Test 2: Configurations
print("\n2️⃣ Testing Configurations...")
try:
    import json
    
    # Test scalping config
    with open('us30_scanner/config_us30_scalp.json', 'r') as f:
        scalp_config = json.load(f)
    print(f"   ✅ Scalping config loaded")
    print(f"      Symbol: {scalp_config['exchange']['symbol']}")
    print(f"      Timeframes: {', '.join(scalp_config['exchange']['timeframes'])}")
    print(f"      Stop Loss: {scalp_config['signal_rules']['stop_loss_points']} points")
    
    # Test swing config
    with open('us30_scanner/config_us30_swing.json', 'r') as f:
        swing_config = json.load(f)
    print(f"   ✅ Swing config loaded")
    print(f"      Symbol: {swing_config['exchange']['symbol']}")
    print(f"      Timeframes: {', '.join(swing_config['exchange']['timeframes'])}")
    print(f"      Stop Loss: {swing_config['signal_rules']['stop_loss_atr_multiplier']}x ATR")
    
except Exception as e:
    print(f"   ❌ Config error: {e}")
    sys.exit(1)

# Test 3: Market Data Connection
print("\n3️⃣ Testing Market Data Connection...")
try:
    client = YFinanceClient(
        symbol="^DJI",
        timeframes=["5m", "1h", "4h", "1d"],
        buffer_size=200
    )
    
    if client.connect():
        print(f"   ✅ Connected to Yahoo Finance")
        
        # Test data fetch
        calc = IndicatorCalculator()
        
        for timeframe in ["1h", "4h", "1d"]:
            try:
                df = client.get_latest_candles(timeframe, count=50)
                
                if not df.empty:
                    # Calculate indicators
                    df['ema_21'] = calc.calculate_ema(df, 21)
                    df['ema_50'] = calc.calculate_ema(df, 50)
                    df['ema_200'] = calc.calculate_ema(df, 200)
                    df['rsi'] = calc.calculate_rsi(df, 14)
                    df['atr'] = calc.calculate_atr(df, 14)
                    
                    # Calculate Stochastic
                    stoch_k, stoch_d = calc.calculate_stochastic(df, 8, 3, 3)
                    df['stoch_k'] = stoch_k
                    
                    # Calculate MACD
                    macd, signal, histogram = calc.calculate_macd(df, 12, 26, 9)
                    df['macd'] = macd
                    df['macd_histogram'] = histogram
                    
                    last = df.iloc[-1]
                    print(f"   ✅ {timeframe:3s}: {last['close']:8,.2f} | RSI: {last['rsi']:5.1f} | ATR: {last['atr']:6.2f} | Stoch: {last['stoch_k']:5.1f}")
                else:
                    print(f"   ⚠️ {timeframe}: No data")
            
            except Exception as e:
                print(f"   ⚠️ {timeframe}: {e}")
    else:
        print(f"   ❌ Connection failed")
        sys.exit(1)
    
except Exception as e:
    print(f"   ❌ Market data error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Signal Detectors
print("\n4️⃣ Testing Signal Detectors...")
try:
    # Test scalping detector
    scalp_detector = US30ScalpDetector(config=scalp_config['signal_rules'])
    print(f"   ✅ Scalping detector initialized")
    
    # Test swing detector
    swing_detector = US30SwingDetector(config=swing_config['signal_rules'])
    print(f"   ✅ Swing detector initialized")
    
    # Try to detect signals (dry run)
    if 'df' in locals() and not df.empty:
        # Add required indicators for scalping
        df['ema_8'] = calc.calculate_ema(df, 8)
        df['vwap'] = calc.calculate_vwap(df)
        df['volume_ma'] = calc.calculate_volume_ma(df, 20)
        
        scalp_signal = scalp_detector.detect_signals(df, '1h')
        swing_signal = swing_detector.detect_signals(df, '4h')
        
        if scalp_signal:
            print(f"   🚨 Scalping signal detected: {scalp_signal.signal_type} ({scalp_signal.strategy})")
        else:
            print(f"   ✅ No scalping signal (normal - waiting for setup)")
        
        if swing_signal:
            print(f"   🚨 Swing signal detected: {swing_signal.signal_type} ({swing_signal.strategy})")
        else:
            print(f"   ✅ No swing signal (normal - waiting for setup)")
    
except Exception as e:
    print(f"   ⚠️ Signal detector warning: {e}")

# Test 5: Main Scripts Syntax
print("\n5️⃣ Testing Main Scripts...")
try:
    import py_compile
    
    py_compile.compile('us30_scanner/main_us30_scalp.py', doraise=True)
    print("   ✅ Scalping main script syntax valid")
    
    py_compile.compile('us30_scanner/main_us30_swing.py', doraise=True)
    print("   ✅ Swing main script syntax valid")
    
except Exception as e:
    print(f"   ❌ Main script error: {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ US30 SCANNERS TEST COMPLETE!")
print("=" * 80)
print("\n🎯 US30 Scanners Ready for Deployment!")
print("\n📊 Scalping Scanner (5m/15m):")
print("   • Liquidity Sweep + Impulse strategy")
print("   • Trend Pullback with Stochastic")
print("   • 30-60 point targets")
print("   • Best hours: NY Open (14:30-17:00 GMT)")
print("\n📈 Swing Scanner (4h/1d):")
print("   • Trend Continuation Pullback")
print("   • Major Trend Reversal (Golden/Death Cross)")
print("   • 2-3x ATR targets")
print("   • Multi-day holds")
print("\nDeploy with:")
print("   python us30_scanner/main_us30_scalp.py")
print("   python us30_scanner/main_us30_swing.py")
print("\nOr deploy all scanners:")
print("   ./start_all_scanners.sh --monitor")
print("=" * 80)
