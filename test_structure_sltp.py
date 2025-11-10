"""Test structure-based SL/TP calculator with live data"""
from src.yfinance_client import YFinanceClient
from src.indicator_calculator import IndicatorCalculator
from src.sl_tp_calculator import SLTPCalculator

def test_structure_sltp():
    """Test structure-based SL/TP on live BTC data"""
    print("=" * 80)
    print("Testing Structure-Based SL/TP Calculator")
    print("=" * 80)
    
    # Fetch live BTC data
    print("\nFetching live BTC 5m data...")
    client = YFinanceClient('BTC-USD', ['5m'], 200)
    client.connect()
    data = client.get_latest_candles('5m', 200)
    
    calc = IndicatorCalculator()
    data = calc.calculate_all_indicators(data)
    
    current_price = data['close'].iloc[-1]
    atr = data['atr'].iloc[-1]
    
    print(f"Current BTC Price: ${current_price:,.2f}")
    print(f"ATR: ${atr:.2f}")
    
    # Test LONG setup
    print("\n" + "=" * 80)
    print("LONG Setup (Structure-Based)")
    print("=" * 80)
    
    sl_long, tp_long, rr_long = SLTPCalculator.calculate_structure_based_sltp(
        data=data,
        entry_price=current_price,
        signal_type="LONG",
        atr=atr,
        lookback=50,
        min_rr=1.5,
        max_rr=5.0
    )
    
    print(f"\nEntry Price: ${current_price:,.2f}")
    print(f"Stop Loss:   ${sl_long:,.2f} (${current_price - sl_long:,.2f} risk = {((current_price - sl_long) / current_price * 100):.2f}%)")
    print(f"Take Profit: ${tp_long:,.2f} (${tp_long - current_price:,.2f} reward = {((tp_long - current_price) / current_price * 100):.2f}%)")
    print(f"Risk/Reward: {rr_long:.2f}:1")
    
    # Compare with old ATR-based method
    print("\n" + "-" * 80)
    print("OLD Method (Fixed ATR Multipliers)")
    print("-" * 80)
    old_sl = current_price - (atr * 1.0)
    old_tp = current_price + (atr * 2.5)
    old_rr = (old_tp - current_price) / (current_price - old_sl)
    
    print(f"\nEntry Price: ${current_price:,.2f}")
    print(f"Stop Loss:   ${old_sl:,.2f} (${current_price - old_sl:,.2f} risk = {((current_price - old_sl) / current_price * 100):.2f}%)")
    print(f"Take Profit: ${old_tp:,.2f} (${old_tp - current_price:,.2f} reward = {((old_tp - current_price) / current_price * 100):.2f}%)")
    print(f"Risk/Reward: {old_rr:.2f}:1")
    
    # Test SHORT setup
    print("\n" + "=" * 80)
    print("SHORT Setup (Structure-Based)")
    print("=" * 80)
    
    sl_short, tp_short, rr_short = SLTPCalculator.calculate_structure_based_sltp(
        data=data,
        entry_price=current_price,
        signal_type="SHORT",
        atr=atr,
        lookback=50,
        min_rr=1.5,
        max_rr=5.0
    )
    
    print(f"\nEntry Price: ${current_price:,.2f}")
    print(f"Stop Loss:   ${sl_short:,.2f} (${sl_short - current_price:,.2f} risk = {((sl_short - current_price) / current_price * 100):.2f}%)")
    print(f"Take Profit: ${tp_short:,.2f} (${current_price - tp_short:,.2f} reward = {((current_price - tp_short) / current_price * 100):.2f}%)")
    print(f"Risk/Reward: {rr_short:.2f}:1")
    
    # Compare with old ATR-based method
    print("\n" + "-" * 80)
    print("OLD Method (Fixed ATR Multipliers)")
    print("-" * 80)
    old_sl_short = current_price + (atr * 1.0)
    old_tp_short = current_price - (atr * 2.5)
    old_rr_short = (current_price - old_tp_short) / (old_sl_short - current_price)
    
    print(f"\nEntry Price: ${current_price:,.2f}")
    print(f"Stop Loss:   ${old_sl_short:,.2f} (${old_sl_short - current_price:,.2f} risk = {((old_sl_short - current_price) / current_price * 100):.2f}%)")
    print(f"Take Profit: ${old_tp_short:,.2f} (${current_price - old_tp_short:,.2f} reward = {((current_price - old_tp_short) / current_price * 100):.2f}%)")
    print(f"Risk/Reward: {old_rr_short:.2f}:1")
    
    # Show recent swing points
    print("\n" + "=" * 80)
    print("Recent Market Structure (Last 50 candles)")
    print("=" * 80)
    
    recent = data.iloc[-50:]
    swing_highs = []
    swing_lows = []
    
    highs = recent['high'].values
    lows = recent['low'].values
    
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append(highs[i])
        
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append(lows[i])
    
    print(f"\nSwing Highs Found: {len(swing_highs)}")
    if swing_highs:
        for i, high in enumerate(sorted(swing_highs, reverse=True)[:5], 1):
            distance = ((high - current_price) / current_price * 100)
            print(f"  {i}. ${high:,.2f} ({distance:+.2f}% from current)")
    
    print(f"\nSwing Lows Found: {len(swing_lows)}")
    if swing_lows:
        for i, low in enumerate(sorted(swing_lows, reverse=True)[:5], 1):
            distance = ((low - current_price) / current_price * 100)
            print(f"  {i}. ${low:,.2f} ({distance:+.2f}% from current)")
    
    print("\n" + "=" * 80)
    print("✅ Structure-based SL/TP uses these swing points for realistic targets!")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    test_structure_sltp()
