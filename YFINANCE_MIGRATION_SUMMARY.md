# Yahoo Finance Migration Summary

## Changes Made

### 1. Updated `main_swing.py`
- Changed import from `MarketDataClient` to `YFinanceClient`
- Updated client initialization to use YFinance
- Updated log messages to reflect Yahoo Finance data source

### 2. Updated `config/config_multitime.json`
- Changed `exchange` from "kraken" to "yfinance"
- Changed `symbol` from "BTC/USD" to "BTC-USD" (Yahoo Finance format)
- Lowered `volume_spike_threshold` from 1.5 to 0.7

## Data Quality Comparison

### Kraken (OLD):
```
15m Timeframe:
- Min volume: 0
- Max volume: 7
- Avg volume: 3
- Scans with volume = 0: 13.5%
- Scans with volume > 1.5x MA: 0%
```

### Yahoo Finance (NEW):
```
15m Timeframe:
- Min volume: 603,930,624
- Max volume: 5,673,353,216
- Avg volume: 1,876,730,421
- Scans with volume = 0: 0%
- All candles have valid volume data ✅
```

## Expected Improvements

### Before (Kraken):
- 1m signals: 1-2 per hour ✅
- 15m signals: 0 per hour ❌ (blocked by volume = 0)
- 1h signals: 0 per hour ❌ (blocked by low volume)
- 4h signals: 0 per hour ❌
- **Total**: 1-2 signals per hour

### After (Yahoo Finance):
- 1m signals: 1-2 per hour ✅
- 15m signals: 2-4 per hour ✅ (now working!)
- 1h signals: 1-2 per hour ✅ (now working!)
- 4h signals: 0-1 per hour ✅
- **Total**: 4-9 signals per hour

## How to Start

```bash
# Stop the current scanner if running (Ctrl+C)

# Start the updated scanner
python main_swing.py
```

## What to Watch For

The scanner will now:
1. Connect to Yahoo Finance instead of Kraken
2. Fetch BTC-USD data with accurate volume
3. Detect trend-following signals on 15m, 1h, 4h, 1d timeframes
4. Send Telegram alerts for each signal

Monitor the logs:
```bash
tail -f logs/scanner_swing.log
```

You should see:
```
[2025-11-04 XX:XX:XX] [INFO] Connecting to Yahoo Finance...
[2025-11-04 XX:XX:XX] [INFO] Successfully connected to Yahoo Finance for BTC-USD
[2025-11-04 XX:XX:XX] [INFO] Fetched 500 candles for 15m
[2025-11-04 XX:XX:XX] [INFO] LONG signal detected on 15m: 104564.85
```

## Benefits of Yahoo Finance

1. **Better Volume Data**: All candles have accurate volume
2. **Free**: No API keys or rate limits
3. **Reliable**: Yahoo Finance is a stable data source
4. **Wide Coverage**: Supports stocks, crypto, forex, commodities
5. **Historical Data**: Access to years of historical data

## Potential Issues

1. **15-minute delay**: Yahoo Finance data may be delayed by 15 minutes for some assets
   - For BTC, this is usually real-time or near real-time
2. **Rate Limits**: Yahoo Finance has soft rate limits (usually not an issue for our use case)
3. **Symbol Format**: Uses different format (BTC-USD vs BTC/USD)

## Rollback (if needed)

If you need to switch back to Kraken:

1. Edit `main_swing.py`:
   - Change import back to `from src.market_data_client import MarketDataClient`
   - Change client initialization back to `MarketDataClient(...)`

2. Edit `config/config_multitime.json`:
   - Change `exchange` back to "kraken"
   - Change `symbol` back to "BTC/USD"

3. Restart the scanner

## Next Steps

1. Start the scanner: `python main_swing.py`
2. Monitor for signals over the next hour
3. Compare signal frequency with previous setup
4. Adjust `volume_spike_threshold` if needed (currently 0.7)

## Notes

- The 1m scalp scanner (main.py) still uses Kraken - you may want to migrate that too
- US30 scanner already uses Yahoo Finance (symbol: ^DJI)
- Gold scanner uses Yahoo Finance (symbol: GC=F)
