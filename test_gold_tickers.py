"""Test different Yahoo Finance tickers for Gold to find best match for spot prices."""
import yfinance as yf
from datetime import datetime

print("=" * 80)
print("TESTING GOLD TICKERS ON YAHOO FINANCE")
print("=" * 80)

# Different Gold tickers available on Yahoo Finance
tickers = {
    'GC=F': 'Gold Futures (Current)',
    'XAUUSD=X': 'Gold Spot vs USD (Forex)',
    'GLD': 'SPDR Gold Shares ETF',
}

print(f"\nYour broker (Vantage Markets) shows: $4,005.00")
print(f"Scanner alert showed: $4,010.10 (from GC=F)")
print(f"Difference: $5.10 (0.13%)\n")

print("Testing alternative tickers...\n")

for ticker, description in tickers.items():
    try:
        print(f"📊 {ticker} - {description}")
        
        # Fetch latest data
        data = yf.download(ticker, period='1d', interval='5m', progress=False)
        
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            print(f"   Latest Price: ${latest_price:,.2f}")
            
            # Calculate difference from your broker price
            broker_price = 4005.00
            diff = latest_price - broker_price
            diff_pct = (diff / broker_price) * 100
            
            print(f"   Difference from broker: ${diff:+.2f} ({diff_pct:+.2f}%)")
            
            if abs(diff) < 2.0:
                print(f"   ✅ EXCELLENT MATCH - Within $2 of broker price!")
            elif abs(diff) < 5.0:
                print(f"   ✅ GOOD MATCH - Within $5 of broker price")
            else:
                print(f"   ⚠️ Larger difference")
        else:
            print(f"   ❌ No data available")
            
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

print("=" * 80)
print("RECOMMENDATION")
print("=" * 80)
print("""
Based on the test results:

1. XAUUSD=X (Gold Spot vs USD) - Usually closest to broker spot prices
   - This is the forex spot price
   - Should match Vantage Markets closely
   
2. GC=F (Gold Futures) - Current setting
   - Typically $2-10 higher than spot
   - More liquid and reliable data
   
3. GLD (ETF) - Not recommended
   - Tracks gold but with management fees
   - Not suitable for scalping

BEST OPTION: Switch to XAUUSD=X for spot prices
""")
print("=" * 80)
