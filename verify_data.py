"""Quick script to verify Kraken data quality and current market conditions."""
import ccxt
import pandas as pd
from datetime import datetime
from src.indicator_calculator import IndicatorCalculator

def verify_kraken_data():
    """Verify Kraken is providing good data and show current market state."""
    print("=" * 80)
    print("KRAKEN DATA VERIFICATION & MARKET STATE")
    print("=" * 80)
    
    # Initialize exchange
    exchange = ccxt.kraken()
    
    # Fetch recent data
    print("\n📊 Fetching BTC/USD data from Kraken...")
    ohlcv_1m = exchange.fetch_ohlcv('BTC/USD', '1m', limit=100)
    ohlcv_5m = exchange.fetch_ohlcv('BTC/USD', '5m', limit=100)
    
    # Convert to DataFrame
    df_1m = pd.DataFrame(ohlcv_1m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_1m['timestamp'] = pd.to_datetime(df_1m['timestamp'], unit='ms')
    
    df_5m = pd.DataFrame(ohlcv_5m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_5m['timestamp'] = pd.to_datetime(df_5m['timestamp'], unit='ms')
    
    # Calculate indicators
    calc = IndicatorCalculator()
    
    # Calculate for 1m
    df_1m['ema_9'] = calc.calculate_ema(df_1m, 9)
    df_1m['ema_21'] = calc.calculate_ema(df_1m, 21)
    df_1m['ema_50'] = calc.calculate_ema(df_1m, 50)
    df_1m['vwap'] = calc.calculate_vwap(df_1m)
    df_1m['atr'] = calc.calculate_atr(df_1m, 14)
    df_1m['rsi'] = calc.calculate_rsi(df_1m, 14)
    df_1m['volume_ma'] = calc.calculate_volume_ma(df_1m, 20)
    
    # Calculate for 5m
    df_5m['ema_9'] = calc.calculate_ema(df_5m, 9)
    df_5m['ema_21'] = calc.calculate_ema(df_5m, 21)
    df_5m['ema_50'] = calc.calculate_ema(df_5m, 50)
    df_5m['vwap'] = calc.calculate_vwap(df_5m)
    df_5m['atr'] = calc.calculate_atr(df_5m, 14)
    df_5m['rsi'] = calc.calculate_rsi(df_5m, 14)
    df_5m['volume_ma'] = calc.calculate_volume_ma(df_5m, 20)
    
    # Show latest data
    last_1m = df_1m.iloc[-1]
    last_5m = df_5m.iloc[-1]
    
    print(f"\n✅ Data Quality Check:")
    print(f"   • 1m candles: {len(df_1m)} received")
    print(f"   • 5m candles: {len(df_5m)} received")
    print(f"   • Latest 1m timestamp: {last_1m['timestamp']}")
    print(f"   • Current BTC price: ${last_1m['close']:,.2f}")
    
    print(f"\n📈 1-MINUTE TIMEFRAME:")
    print(f"   Price: ${last_1m['close']:,.2f}")
    print(f"   VWAP: ${last_1m['vwap']:,.2f} ({'ABOVE' if last_1m['close'] > last_1m['vwap'] else 'BELOW'})")
    print(f"   EMA(9): ${last_1m['ema_9']:,.2f}")
    print(f"   EMA(21): ${last_1m['ema_21']:,.2f} ({'BULLISH' if last_1m['ema_9'] > last_1m['ema_21'] else 'BEARISH'} cross)")
    print(f"   EMA(50): ${last_1m['ema_50']:,.2f}")
    print(f"   RSI: {last_1m['rsi']:.1f}")
    print(f"   Volume: {last_1m['volume']:,.0f} (Avg: {last_1m['volume_ma']:,.0f})")
    print(f"   Volume Ratio: {last_1m['volume'] / last_1m['volume_ma']:.2f}x")
    print(f"   ATR: ${last_1m['atr']:.2f}")
    
    print(f"\n📊 5-MINUTE TIMEFRAME:")
    print(f"   Price: ${last_5m['close']:,.2f}")
    print(f"   VWAP: ${last_5m['vwap']:,.2f} ({'ABOVE' if last_5m['close'] > last_5m['vwap'] else 'BELOW'})")
    print(f"   EMA(9): ${last_5m['ema_9']:,.2f}")
    print(f"   EMA(21): ${last_5m['ema_21']:,.2f} ({'BULLISH' if last_5m['ema_9'] > last_5m['ema_21'] else 'BEARISH'} cross)")
    print(f"   EMA(50): ${last_5m['ema_50']:,.2f}")
    print(f"   RSI: {last_5m['rsi']:.1f}")
    print(f"   Volume: {last_5m['volume']:,.0f} (Avg: {last_5m['volume_ma']:,.0f})")
    print(f"   Volume Ratio: {last_5m['volume'] / last_5m['volume_ma']:.2f}x")
    print(f"   ATR: ${last_5m['atr']:.2f}")
    
    # Check signal conditions
    print(f"\n🔍 SIGNAL REQUIREMENTS CHECK (1m):")
    checks = []
    checks.append(("Price > VWAP", last_1m['close'] > last_1m['vwap']))
    
    prev_1m = df_1m.iloc[-2]
    ema_cross_bull = last_1m['ema_9'] > last_1m['ema_21'] and prev_1m['ema_9'] <= prev_1m['ema_21']
    ema_cross_bear = last_1m['ema_9'] < last_1m['ema_21'] and prev_1m['ema_9'] >= prev_1m['ema_21']
    checks.append(("EMA Crossover (recent)", ema_cross_bull or ema_cross_bear))
    
    checks.append(("Volume > 1.5x avg", last_1m['volume'] > last_1m['volume_ma'] * 1.5))
    checks.append(("RSI 30-70", 30 <= last_1m['rsi'] <= 70))
    
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {check_name}")
    
    passed_count = sum(1 for _, p in checks if p)
    print(f"\n   Total: {passed_count}/4 critical factors met")
    
    if passed_count < 4:
        print(f"\n💡 No signal because not all 4 critical factors aligned.")
        print(f"   This is NORMAL - we wait for high-probability setups only.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    verify_kraken_data()
