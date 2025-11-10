"""Quick script to check ATR values for different assets"""
from src.yfinance_client import YFinanceClient
from src.indicator_calculator import IndicatorCalculator

assets = [
    ('BTC-USD', '5m', 'BTC 5min'),
    ('^DJI', '5m', 'US30 5min'),
    ('GC=F', '5m', 'Gold 5min'),
]

for symbol, tf, name in assets:
    try:
        client = YFinanceClient(symbol, [tf], 200)
        client.connect()
        data = client.get_latest_candles(tf, 200)
        calc = IndicatorCalculator()
        result = calc.calculate_all_indicators(data)
        
        atr = result['atr'].iloc[-1]
        price = result['close'].iloc[-1]
        atr_pct = (atr / price) * 100
        
        print(f"\n{name}:")
        print(f"  Price: ${price:,.2f}")
        print(f"  ATR: ${atr:,.2f}")
        print(f"  ATR as % of price: {atr_pct:.3f}%")
        print(f"  OLD - 1.5x ATR SL: ${atr * 1.5:,.2f} ({atr_pct * 1.5:.3f}%) | 1.0x ATR TP: ${atr * 1.0:,.2f} | R:R: 0.67 ❌")
        print(f"  NEW - 1.0x ATR SL: ${atr * 1.0:,.2f} ({atr_pct * 1.0:.3f}%) | 2.5x ATR TP: ${atr * 2.5:,.2f} | R:R: 2.50 ✅")
        
        client.close()
    except Exception as e:
        print(f"\n{name}: Error - {e}")
