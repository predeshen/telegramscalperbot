# BTC Swing Trading Scanner Guide

## Overview
The swing scanner monitors **15m, 1h, 4h, and 1d** timeframes for longer-term trading opportunities.

## Key Differences from Scalping Scanner

| Feature | Scalping (1m/5m) | Swing (15m/1h/4h/1d) |
|---------|------------------|----------------------|
| **Timeframes** | 1 minute, 5 minutes | 15 min, 1 hour, 4 hours, 1 day |
| **Hold Time** | Minutes to hours | Hours to days |
| **Check Frequency** | Every 10 seconds | Every 60 seconds |
| **Stop Loss** | 1.5x ATR | 2.0x ATR (wider) |
| **Take Profit** | 1.0x ATR | 1.5x ATR (larger) |
| **Signals/Day** | 2-10 | 1-3 |
| **Risk/Reward** | 0.67:1 | 0.75:1 |

## Deployment

### On Linux VM:
```bash
# Make executable
chmod +x deploy_swing_scanner.sh

# Deploy
./deploy_swing_scanner.sh
```

### Manual Start:
```bash
# Start in screen
screen -S btc_swing
python main_swing.py

# Detach: Ctrl+A, then D
```

## Monitoring

### View Logs:
```bash
tail -f logs/scanner_swing.log
```

### Check Status:
```bash
screen -list
# Should show: btc_swing
```

### Attach to Session:
```bash
screen -r btc_swing
# Detach: Ctrl+A, then D
```

## Configuration

Edit `config/config_multitime.json`:

```json
{
  "timeframes": ["15m", "1h", "4h", "1d"],
  "polling_interval_seconds": 60,
  "signal_detection": {
    "stop_loss_atr_multiplier": 2.0,
    "take_profit_atr_multiplier": 1.5,
    "duplicate_time_window_minutes": 60
  }
}
```

## Strategy

### 15-Minute Timeframe
- **Best for**: Intraday swings
- **Hold time**: 1-4 hours
- **Target**: 0.5-1% moves

### 1-Hour Timeframe
- **Best for**: Daily swings
- **Hold time**: 4-24 hours
- **Target**: 1-2% moves

### 4-Hour Timeframe
- **Best for**: Multi-day swings
- **Hold time**: 1-3 days
- **Target**: 2-5% moves

### Daily Timeframe
- **Best for**: Position trading
- **Hold time**: Days to weeks
- **Target**: 5-10% moves

## Signal Quality

Same confluence requirements as scalping:
1. Price vs VWAP
2. EMA(9) crosses EMA(21)
3. Volume spike (1.5x average)
4. RSI 30-70

But on higher timeframes = bigger moves!

## Running Both Scanners

You can run both simultaneously:

```bash
# Scalping scanner (already running)
screen -r btc_scanner

# Swing scanner (new)
screen -r btc_swing
```

They work independently and send separate Telegram alerts.

## Stopping

```bash
# Stop swing scanner
screen -X -S btc_swing quit

# Or attach and Ctrl+C
screen -r btc_swing
# Then Ctrl+C
```

## Troubleshooting

### Scanner not starting?
```bash
# Check Python
python --version

# Test manually
python main_swing.py
```

### No signals?
- Normal! Higher timeframes = fewer but better signals
- Check logs: `tail -f logs/scanner_swing.log`
- Verify data: `python verify_data.py`

### Telegram not working?
```bash
# Check environment variables
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

## Expected Performance

- **Signals per day**: 1-3 quality setups
- **Win rate**: Similar to scalping (~60-70%)
- **Average R:R**: 0.75:1 (wider stops, bigger targets)
- **Best timeframe**: 1h and 4h for balance

## Tips

1. **Combine with scalping** - Use swing for direction, scalp in that direction
2. **Higher timeframes = more reliable** - 4h and 1d signals are strongest
3. **Be patient** - Fewer signals but bigger moves
4. **Trail stops** - On 4h/1d, consider trailing stops after 50% to target
