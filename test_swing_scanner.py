"""Test the swing scanner with Yahoo Finance."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.yfinance_client import YFinanceClient
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector

def test_scanner():
    """Test the scanner components."""
    print("=" * 80)
    print("TESTING BTC SWING SCANNER WITH YAHOO FINANCE")
    print("=" * 80)
    
    # Test 1: Connect to Yahoo Finance
    print("\n1. Testing Yahoo Finance Connection...")
    client = YFinanceClient(
        symbol="BTC-USD",
        timeframes=["15m", "1h"],
        buffer_size=500
    )
    
    if client.connect():
        print("   ✅ Successfully connected to Yahoo Finance")
    else:
        print("   ❌ Failed to connect")
        return False
    
    # Test 2: Fetch data
    print("\n2. Testing Data Fetch...")
    try:
        df_15m = client.get_latest_candles("15m", count=100)
        df_1h = client.get_latest_candles("1h", count=100)
        
        print(f"   ✅ Fetched {len(df_15m)} candles for 15m")
        print(f"   ✅ Fetched {len(df_1h)} candles for 1h")
        
        # Check volume data
        print("\n3. Testing Volume Data Quality...")
        vol_15m = df_15m['volume']
        vol_1h = df_1h['volume']
        
        print(f"\n   15m Volume Stats:")
        print(f"      Min: {vol_15m.min():,.0f}")
        print(f"      Max: {vol_15m.max():,.0f}")
        print(f"      Avg: {vol_15m.mean():,.0f}")
        print(f"      Zero values: {(vol_15m == 0).sum()}")
        
        print(f"\n   1h Volume Stats:")
        print(f"      Min: {vol_1h.min():,.0f}")
        print(f"      Max: {vol_1h.max():,.0f}")
        print(f"      Avg: {vol_1h.mean():,.0f}")
        print(f"      Zero values: {(vol_1h == 0).sum()}")
        
        if (vol_15m == 0).sum() == 0 and (vol_1h == 0).sum() == 0:
            print("\n   ✅ All volume data is valid (no zeros)")
        else:
            print("\n   ⚠️  Some volume data is zero")
        
    except Exception as e:
        print(f"   ❌ Failed to fetch data: {e}")
        return False
    
    # Test 3: Calculate indicators
    print("\n4. Testing Indicator Calculation...")
    try:
        indicator_calc = IndicatorCalculator()
        
        # Calculate indicators for 15m
        df_15m['ema_9'] = indicator_calc.calculate_ema(df_15m, 9)
        df_15m['ema_21'] = indicator_calc.calculate_ema(df_15m, 21)
        df_15m['ema_50'] = indicator_calc.calculate_ema(df_15m, 50)
        df_15m['vwap'] = indicator_calc.calculate_vwap(df_15m)
        df_15m['atr'] = indicator_calc.calculate_atr(df_15m, 14)
        df_15m['rsi'] = indicator_calc.calculate_rsi(df_15m, 14)
        df_15m['volume_ma'] = indicator_calc.calculate_volume_ma(df_15m, 20)
        
        print("   ✅ Indicators calculated successfully")
        
        # Show last candle
        last = df_15m.iloc[-1]
        print(f"\n   Last 15m Candle:")
        print(f"      Time: {last['timestamp']}")
        print(f"      Price: ${last['close']:,.2f}")
        print(f"      EMA9: ${last['ema_9']:,.2f}")
        print(f"      EMA21: ${last['ema_21']:,.2f}")
        print(f"      EMA50: ${last['ema_50']:,.2f}")
        print(f"      RSI: {last['rsi']:.1f}")
        print(f"      Volume: {last['volume']:,.0f}")
        print(f"      Volume MA: {last['volume_ma']:,.0f}")
        print(f"      Volume Ratio: {last['volume'] / last['volume_ma']:.2f}x")
        
    except Exception as e:
        print(f"   ❌ Failed to calculate indicators: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Signal detection
    print("\n5. Testing Signal Detection...")
    try:
        signal_detector = SignalDetector(
            volume_spike_threshold=0.7,
            rsi_min=30,
            rsi_max=70,
            stop_loss_atr_multiplier=2.0,
            take_profit_atr_multiplier=1.5,
            duplicate_time_window_minutes=60,
            duplicate_price_threshold_percent=0.5
        )
        
        signal = signal_detector.detect_signals(df_15m, "15m", symbol="BTC/USD")
        
        if signal:
            print(f"   🎯 SIGNAL DETECTED!")
            print(f"      Type: {signal.signal_type}")
            print(f"      Strategy: {signal.strategy}")
            print(f"      Entry: ${signal.entry_price:,.2f}")
            print(f"      Stop Loss: ${signal.stop_loss:,.2f}")
            print(f"      Take Profit: ${signal.take_profit:,.2f}")
            print(f"      Risk/Reward: 1:{signal.risk_reward:.2f}")
            print(f"      Confidence: {signal.confidence}/5")
        else:
            print("   ℹ️  No signal detected (this is normal)")
            print("      Checking signal requirements...")
            
            last = df_15m.iloc[-1]
            prev = df_15m.iloc[-2]
            
            # Check EMA crossover
            if last['ema_9'] > last['ema_21'] and prev['ema_9'] <= prev['ema_21']:
                print("      ✅ Bullish EMA crossover detected")
            elif last['ema_9'] < last['ema_21'] and prev['ema_9'] >= prev['ema_21']:
                print("      ✅ Bearish EMA crossover detected")
            else:
                print("      ❌ No EMA crossover")
            
            # Check volume
            vol_ratio = last['volume'] / last['volume_ma']
            if vol_ratio >= 0.7:
                print(f"      ✅ Volume sufficient ({vol_ratio:.2f}x)")
            else:
                print(f"      ❌ Volume too low ({vol_ratio:.2f}x < 0.7x)")
            
            # Check RSI
            if 30 <= last['rsi'] <= 70:
                print(f"      ✅ RSI in range ({last['rsi']:.1f})")
            else:
                print(f"      ❌ RSI out of range ({last['rsi']:.1f})")
            
            # Check VWAP
            if last['close'] > last['vwap']:
                print(f"      ✅ Price above VWAP (bullish)")
            elif last['close'] < last['vwap']:
                print(f"      ✅ Price below VWAP (bearish)")
            else:
                print(f"      ℹ️  Price at VWAP")
        
        print("\n   ✅ Signal detection working correctly")
        
    except Exception as e:
        print(f"   ❌ Failed to detect signals: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Check for trend-following opportunities
    print("\n6. Checking for Trend-Following Opportunities...")
    try:
        last = df_15m.iloc[-1]
        
        # Check if price near EMA21
        distance_pct = abs(last['close'] - last['ema_21']) / last['close'] * 100
        
        if distance_pct < 0.5:
            print(f"   📍 Price near EMA21 ({distance_pct:.2f}% away)")
            print(f"      This could trigger a trend-following signal with volume confirmation")
        else:
            print(f"   ℹ️  Price {distance_pct:.2f}% away from EMA21")
        
        # Check EMA alignment
        if last['ema_9'] > last['ema_21'] > last['ema_50']:
            print(f"   ✅ Bullish EMA alignment (9 > 21 > 50)")
        elif last['ema_9'] < last['ema_21'] < last['ema_50']:
            print(f"   ✅ Bearish EMA alignment (9 < 21 < 50)")
        else:
            print(f"   ℹ️  Mixed EMA alignment")
        
    except Exception as e:
        print(f"   ⚠️  Could not check trend opportunities: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY ✅")
    print("=" * 80)
    print("\nThe scanner is ready to run. Start it with:")
    print("  python main_swing.py")
    print("\nMonitor logs with:")
    print("  tail -f logs/scanner_swing.log")
    
    return True


if __name__ == "__main__":
    try:
        success = test_scanner()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
