"""Analyze potential missed signals from Excel scan data."""
import pandas as pd
from datetime import datetime

def analyze_missed_signals():
    """Analyze why signals were or weren't detected."""
    
    # Load BTC swing scanner data
    df = pd.read_excel('excell/btc_swing_scans (1).xlsx')
    
    # Filter for time period around your signal (02:00-03:00 UTC)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    recent = df[(df['timestamp'] >= '2025-11-04 02:00:00') & 
                (df['timestamp'] <= '2025-11-04 03:00:00')]
    
    print("=" * 80)
    print("MISSED SIGNAL ANALYSIS - BTC Swing Scanner")
    print("=" * 80)
    print(f"\nTotal scans in period: {len(recent)}")
    print(f"Signals detected: {recent['signal_detected'].sum()}")
    
    # Analyze each timeframe
    for tf in ['15m', '1h', '4h', '1d']:
        tf_data = recent[recent['timeframe'] == tf]
        if len(tf_data) == 0:
            continue
            
        print(f"\n{'=' * 80}")
        print(f"TIMEFRAME: {tf}")
        print(f"{'=' * 80}")
        
        # Check for EMA crossover opportunities
        print("\n1. EMA CROSSOVER ANALYSIS:")
        for i in range(1, len(tf_data)):
            curr = tf_data.iloc[i]
            prev = tf_data.iloc[i-1]
            
            # Bullish crossover
            if curr['ema_9'] > curr['ema_21'] and prev['ema_9'] <= prev['ema_21']:
                vol_ratio = curr['volume'] / curr['volume_ma'] if curr['volume_ma'] > 0 else 0
                print(f"\n   🔵 BULLISH CROSSOVER at {curr['timestamp']}")
                print(f"      Price: ${curr['price']:,.2f}")
                print(f"      EMA9: ${curr['ema_9']:,.2f} > EMA21: ${curr['ema_21']:,.2f}")
                print(f"      Volume: {curr['volume']:,.0f} ({vol_ratio:.2f}x avg)")
                print(f"      RSI: {curr['rsi']:.1f}")
                print(f"      VWAP: ${curr['vwap']:,.2f}")
                
                # Check why it didn't trigger
                reasons = []
                if curr['price'] <= curr['vwap']:
                    reasons.append(f"❌ Price (${curr['price']:,.2f}) <= VWAP (${curr['vwap']:,.2f})")
                if vol_ratio < 1.5:
                    reasons.append(f"❌ Volume ({vol_ratio:.2f}x) < 1.5x threshold")
                if not (30 <= curr['rsi'] <= 70):
                    reasons.append(f"❌ RSI ({curr['rsi']:.1f}) outside 30-70 range")
                if curr['price'] <= curr['ema_50']:
                    reasons.append(f"❌ Price (${curr['price']:,.2f}) <= EMA50 (${curr['ema_50']:,.2f})")
                
                if reasons:
                    print(f"\n      WHY NO SIGNAL:")
                    for reason in reasons:
                        print(f"      {reason}")
                else:
                    print(f"\n      ✅ ALL CONDITIONS MET - SHOULD HAVE SIGNALED!")
            
            # Bearish crossover
            elif curr['ema_9'] < curr['ema_21'] and prev['ema_9'] >= prev['ema_21']:
                vol_ratio = curr['volume'] / curr['volume_ma'] if curr['volume_ma'] > 0 else 0
                print(f"\n   🔴 BEARISH CROSSOVER at {curr['timestamp']}")
                print(f"      Price: ${curr['price']:,.2f}")
                print(f"      EMA9: ${curr['ema_9']:,.2f} < EMA21: ${curr['ema_21']:,.2f}")
                print(f"      Volume: {curr['volume']:,.0f} ({vol_ratio:.2f}x avg)")
                print(f"      RSI: {curr['rsi']:.1f}")
                
                # Check why it didn't trigger
                reasons = []
                if curr['price'] >= curr['vwap']:
                    reasons.append(f"❌ Price (${curr['price']:,.2f}) >= VWAP (${curr['vwap']:,.2f})")
                if vol_ratio < 1.5:
                    reasons.append(f"❌ Volume ({vol_ratio:.2f}x) < 1.5x threshold")
                if not (30 <= curr['rsi'] <= 70):
                    reasons.append(f"❌ RSI ({curr['rsi']:.1f}) outside 30-70 range")
                if curr['price'] >= curr['ema_50']:
                    reasons.append(f"❌ Price (${curr['price']:,.2f}) >= EMA50 (${curr['ema_50']:,.2f})")
                
                if reasons:
                    print(f"\n      WHY NO SIGNAL:")
                    for reason in reasons:
                        print(f"      {reason}")
                else:
                    print(f"\n      ✅ ALL CONDITIONS MET - SHOULD HAVE SIGNALED!")
        
        # Check for trend-following opportunities
        print("\n2. TREND-FOLLOWING ANALYSIS:")
        print(f"   Checking for pullbacks to EMA(21)...")
        
        for i in range(len(tf_data)):
            curr = tf_data.iloc[i]
            vol_ratio = curr['volume'] / curr['volume_ma'] if curr['volume_ma'] > 0 else 0
            
            # Check if price near EMA21
            distance_pct = abs(curr['price'] - curr['ema_21']) / curr['price'] * 100
            
            if distance_pct < 0.5:  # Within 0.5% of EMA21
                print(f"\n   📍 NEAR EMA21 at {curr['timestamp']}")
                print(f"      Price: ${curr['price']:,.2f}, EMA21: ${curr['ema_21']:,.2f} ({distance_pct:.2f}% away)")
                print(f"      Volume: {curr['volume']:,.0f} ({vol_ratio:.2f}x avg)")
                print(f"      RSI: {curr['rsi']:.1f}")
                
                # Check trend-following requirements
                reasons = []
                if vol_ratio < 1.2:
                    reasons.append(f"❌ Volume ({vol_ratio:.2f}x) < 1.2x threshold")
                if curr['volume'] == 0:
                    reasons.append(f"❌ Volume = 0 (DATA QUALITY ISSUE)")
                if not (40 <= curr['rsi'] <= 80):
                    reasons.append(f"❌ RSI ({curr['rsi']:.1f}) outside 40-80 range for uptrend")
                
                if reasons:
                    print(f"      WHY NO SIGNAL:")
                    for reason in reasons:
                        print(f"      {reason}")
                else:
                    print(f"      ✅ POTENTIAL TREND-FOLLOWING SIGNAL")
        
        # Volume statistics
        print(f"\n3. VOLUME STATISTICS:")
        print(f"   Min volume: {tf_data['volume'].min():,.0f}")
        print(f"   Max volume: {tf_data['volume'].max():,.0f}")
        print(f"   Avg volume: {tf_data['volume'].mean():,.0f}")
        print(f"   Avg volume MA: {tf_data['volume_ma'].mean():,.0f}")
        print(f"   Scans with volume = 0: {(tf_data['volume'] == 0).sum()}")
        print(f"   Scans with volume > 1.5x MA: {(tf_data['volume'] > tf_data['volume_ma'] * 1.5).sum()}")
    
    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    
    # Count volume issues
    zero_volume = (recent['volume'] == 0).sum()
    low_volume = (recent['volume'] < recent['volume_ma'] * 1.5).sum()
    
    print(f"\n📊 DATA QUALITY ISSUES:")
    print(f"   Scans with volume = 0: {zero_volume} ({zero_volume/len(recent)*100:.1f}%)")
    print(f"   Scans with volume < 1.5x MA: {low_volume} ({low_volume/len(recent)*100:.1f}%)")
    
    print(f"\n🎯 SIGNAL DETECTION:")
    print(f"   Total signals detected: {recent['signal_detected'].sum()}")
    print(f"   Signal rate: {recent['signal_detected'].sum()/len(recent)*100:.2f}%")
    
    print(f"\n💡 KEY FINDINGS:")
    if zero_volume > len(recent) * 0.5:
        print(f"   ⚠️  CRITICAL: {zero_volume/len(recent)*100:.0f}% of scans have volume = 0")
        print(f"   This prevents volume-based signals from triggering")
        print(f"   Recommendation: Check Kraken API or switch to Binance")
    
    if low_volume > len(recent) * 0.8:
        print(f"   ⚠️  WARNING: {low_volume/len(recent)*100:.0f}% of scans have low volume")
        print(f"   Consider lowering volume_spike_threshold from 1.5 to 1.2")


if __name__ == "__main__":
    analyze_missed_signals()
