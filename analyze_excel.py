"""Analyze Excel scan data to check for missed signals."""
import pandas as pd
import sys
from datetime import datetime

def analyze_scans(excel_file):
    """Analyze scan data from Excel file."""
    try:
        xl = pd.ExcelFile(excel_file)
        print(f"📊 Analyzing: {excel_file}")
        print(f"Sheets found: {xl.sheet_names}\n")
        
        for sheet in xl.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet)
            print("=" * 80)
            print(f"📈 {sheet} - {len(df)} total scans")
            print("=" * 80)
            
            if df.empty:
                print("No data in this sheet\n")
                continue
            
            # Show column names
            print(f"\nColumns: {list(df.columns)}\n")
            
            # Show first 10 rows
            print("First 10 scans:")
            print(df.head(10).to_string())
            
            # Check for signals
            if 'signal_detected' in df.columns:
                signals = df[df['signal_detected'] == True]
                print(f"\n🎯 Signals detected: {len(signals)}")
                
                if len(signals) > 0:
                    print("\nSignal details:")
                    for idx, row in signals.iterrows():
                        print(f"\n  [{row.get('timestamp', 'N/A')}]")
                        print(f"  Type: {row.get('signal_type', 'N/A')}")
                        print(f"  Price: {row.get('price', 'N/A')}")
                        print(f"  Timeframe: {row.get('timeframe', 'N/A')}")
            
            # Analyze price action for potential missed signals
            if 'price' in df.columns and 'timestamp' in df.columns:
                print(f"\n📉 Price Analysis:")
                print(f"  Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
                print(f"  Price change: {((df['price'].iloc[-1] / df['price'].iloc[0]) - 1) * 100:.2f}%")
                
                # Check for downtrend indicators
                if len(df) >= 10:
                    recent = df.tail(10)
                    if 'ema_9' in df.columns and 'ema_21' in df.columns and 'ema_50' in df.columns:
                        last = recent.iloc[-1]
                        print(f"\n  Latest indicators:")
                        print(f"    Price: ${last['price']:.2f}")
                        print(f"    EMA 9: ${last.get('ema_9', 'N/A')}")
                        print(f"    EMA 21: ${last.get('ema_21', 'N/A')}")
                        print(f"    EMA 50: ${last.get('ema_50', 'N/A')}")
                        print(f"    RSI: {last.get('rsi', 'N/A')}")
                        
                        # Check for bearish setup
                        if (last['price'] < last.get('ema_9', float('inf')) and
                            last.get('ema_9', 0) < last.get('ema_21', float('inf')) and
                            last['price'] < last.get('ema_50', float('inf'))):
                            print(f"\n  ⚠️  BEARISH SETUP DETECTED:")
                            print(f"    Price below all EMAs")
                            print(f"    EMA 9 < EMA 21 (bearish alignment)")
                            print(f"    RSI: {last.get('rsi', 'N/A')}")
                            print(f"    This should have triggered a SHORT signal!")
            
            print("\n")
    
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    files = [
        "excell/btc_swing_scans.xlsx",
        "excell/xauusd_scalp_scans.xlsx",
        "excell/xauusd_swing_scans.xlsx",
        "excell/us30_swing_scans.xlsx"
    ]
    
    for file in files:
        try:
            analyze_scans(file)
            print("\n" + "="*100 + "\n")
        except Exception as e:
            print(f"Could not analyze {file}: {e}\n")
