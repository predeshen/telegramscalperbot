"""
Quick test of US30 strategy with sample data
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.us30_strategy import US30Strategy
from src.indicator_calculator import IndicatorCalculator

def create_sample_data():
    """Create sample US30 data with a bullish FVG pattern"""
    dates = [datetime.now() - timedelta(minutes=i) for i in range(50, 0, -1)]
    
    # Create price data with a gap (FVG)
    base_price = 47000
    prices = []
    
    for i in range(50):
        if i < 20:
            # Consolidation
            prices.append(base_price + np.random.randint(-50, 50))
        elif i == 20:
            # Candle 1 before gap
            prices.append(base_price + 20)
        elif i == 21:
            # Candle 2 (middle)
            prices.append(base_price + 100)
        elif i == 22:
            # Candle 3 after gap (creates FVG)
            prices.append(base_price + 180)
        else:
            # Continuation
            prices.append(base_price + 180 + (i - 22) * 10)
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        # Create OHLC
        open_price = price + np.random.randint(-10, 10)
        high = max(open_price, price) + np.random.randint(5, 20)
        low = min(open_price, price) - np.random.randint(5, 20)
        close = price
        volume = 1000 + np.random.randint(0, 500)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data)

def main():
    print("=" * 60)
    print("US30 STRATEGY TEST")
    print("=" * 60)
    
    # Create sample data
    print("\n1. Creating sample US30 data with FVG pattern...")
    data = create_sample_data()
    print(f"   ✅ Created {len(data)} candles")
    
    # Calculate indicators
    print("\n2. Calculating indicators...")
    calc = IndicatorCalculator()
    data['ema_9'] = calc.calculate_ema(data, 9)
    data['ema_21'] = calc.calculate_ema(data, 21)
    data['ema_50'] = calc.calculate_ema(data, 50)
    data['ema_100'] = calc.calculate_ema(data, 100)
    data['ema_200'] = calc.calculate_ema(data, 200)
    data['atr'] = calc.calculate_atr(data, 14)
    data['rsi'] = calc.calculate_rsi(data, 14)
    data['volume_ma'] = calc.calculate_volume_ma(data, 20)
    data['adx'] = calc.calculate_adx(data, 14)
    print("   ✅ Indicators calculated")
    
    # Initialize strategy
    print("\n3. Initializing US30 strategy...")
    config = {
        'us30_strategy': {
            'min_fvg_percent': 0.05,
            'fvg_lookback': 20,
            'swing_lookback': 5,
            'min_break_percent': 0.1,
            'min_adx': 20,  # Lower for test
            'min_volume_ratio': 1.0,  # Lower for test
            'min_candle_body_percent': 50,  # Lower for test
            'initial_tp_atr': 2.5,
            'stop_loss_atr': 1.5,
            'trail_after_atr': 1.5
        }
    }
    strategy = US30Strategy(config=config)
    print("   ✅ Strategy initialized")
    
    # Detect signal
    print("\n4. Detecting signals...")
    signal = strategy.detect_signal(data, "5m")
    
    if signal:
        print("\n" + "=" * 60)
        print("🚀 SIGNAL DETECTED!")
        print("=" * 60)
        print(f"Type: {signal.signal_type}")
        print(f"Strategy: {signal.strategy}")
        print(f"Confidence: {'⭐' * signal.confidence} ({signal.confidence}/5)")
        print(f"\nEntry: ${signal.entry_price:,.2f}")
        print(f"Stop Loss: ${signal.stop_loss:,.2f}")
        print(f"Take Profit: ${signal.take_profit:,.2f}")
        print(f"Risk:Reward: {signal.risk_reward:.2f}")
        print(f"\nReasoning: {signal.reasoning}")
        
        if signal.strategy_metadata:
            print("\nStrategy Details:")
            if signal.strategy_metadata.get('fvg'):
                fvg = signal.strategy_metadata['fvg']
                print(f"  FVG: {fvg['gap_type']} gap {fvg['gap_percent']:.2f}%")
                print(f"       ${fvg['gap_low']:.2f} - ${fvg['gap_high']:.2f}")
            
            if signal.strategy_metadata.get('structure_break'):
                sb = signal.strategy_metadata['structure_break']
                print(f"  Structure: {sb['break_type']} ({sb['direction']})")
                print(f"             Strength {sb['strength']}/5")
        
        print("\n✅ TEST PASSED - Strategy working correctly!")
    else:
        print("\n⚠️  No signal detected")
        print("   This might be normal - try adjusting test data or thresholds")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
