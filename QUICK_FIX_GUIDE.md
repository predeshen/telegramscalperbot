# Quick Fix Guide - Get More Signals

## Problem
You're only getting signals from the 1m scanner because the 15m, 1h, 4h, and 1d scanners have broken volume data from Kraken.

## Evidence
- 15m volume: 0-7 (should be thousands)
- 1h volume: 0-25 (should be tens of thousands)
- 1m volume: Working correctly (18.58x average)
- **100% of swing scanner scans failed the volume check**

## Quick Fix (2 minutes)

### Option 1: Lower Volume Threshold

Edit `config/config_multitime.json`:

```json
{
  "signal_detection": {
    "volume_spike_threshold": 0.5,
    "rsi_min": 30,
    "rsi_max": 70,
    "stop_loss_atr_multiplier": 2.0,
    "take_profit_atr_multiplier": 1.5,
    "duplicate_time_window_minutes": 60,
    "duplicate_price_threshold_percent": 0.5
  }
}
```

**Changed**: `volume_spike_threshold` from 1.5 to 0.5

Then restart the swing scanner:
```bash
# Stop current scanner
Ctrl+C

# Start again
python main_swing.py
```

### Option 2: Switch to Binance (Better Fix)

Edit `config/config_multitime.json`:

```json
{
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "timeframes": ["15m", "1h", "4h", "1d"],
  ...
}
```

**Changed**: 
- `exchange` from "kraken" to "binance"
- `symbol` from "BTC/USD" to "BTC/USDT"

Then restart:
```bash
python main_swing.py
```

## Expected Results

### Before Fix:
- 1m signals: 1-2 per hour ✅
- 15m signals: 0 per hour ❌
- 1h signals: 0 per hour ❌
- **Total**: 1-2 signals per hour

### After Fix:
- 1m signals: 1-2 per hour ✅
- 15m signals: 2-4 per hour ✅
- 1h signals: 1-2 per hour ✅
- 4h signals: 0-1 per hour ✅
- **Total**: 4-9 signals per hour

## Verification

After applying the fix, check the logs:
```bash
tail -f logs/scanner_swing.log
```

You should see messages like:
```
[2025-11-04 XX:XX:XX] [INFO] LONG signal detected on 15m: 106900.1
[2025-11-04 XX:XX:XX] [INFO] Alert sent successfully
```

## Why This Happened

The signal you received at 02:17 UTC was from the **1m scanner** (main.py), which has accurate volume data.

The **swing scanner** (main_swing.py) monitors 15m, 1h, 4h, 1d timeframes, but Kraken's API provides broken volume data for these timeframes.

At 02:17:36 UTC, there was a perfect trend-following setup on 15m:
- Price: $106,900.10
- EMA21: $106,700.44 (perfect pullback)
- RSI: 53.3 (healthy)
- Volume: 0 ❌ (DATA ISSUE)

**This should have been a signal, but volume = 0 blocked it.**

## Recommendation

**Use Option 2 (Switch to Binance)** for the best long-term solution. Binance has more reliable data and higher liquidity.

If you want to keep using Kraken, use Option 1 but be aware that some signals may be lower quality due to the volume data issue.
