# US30 Momentum Scanner - Setup Complete! 🚀

## What Was Created

### New Files
1. **src/fvg_detector.py** - Fair Value Gap detection
2. **src/market_structure.py** - Market structure analysis (BOS/CHoCH)
3. **src/us30_strategy.py** - Aggressive momentum strategy
4. **main_us30.py** - Main scanner application
5. **systemd/us30-momentum-scanner.service** - Systemd service file
6. **start_us30_momentum.bat** - Windows quick start script
7. **test_us30_strategy.py** - Strategy test script

### Updated Files
1. **config/us30_config.json** - Added strategy configuration
2. **start_all_scanners.sh** - Added US30 momentum scanner
3. **restart_scanners.sh** - Added US30 momentum scanner
4. **clean_and_restart.sh** - Added US30 momentum scanner

## Scanner Lineup (All 3 US30 Scanners)

You now have **3 US30 scanners** running in parallel:

1. **US30 Scalp** (existing) - `us30_scalp`
   - Timeframes: 5m, 15m
   - Strategy: Original scalping logic

2. **US30 Swing** (existing) - `us30_swing`
   - Timeframes: 4h, 1d
   - Strategy: Original swing logic

3. **US30 Momentum** (NEW) - `us30_momentum` 🚀
   - Timeframes: 1m, 5m, 15m
   - Strategy: FVG + Structure Breaks + Momentum
   - Target: 2.5 ATR (catches big moves!)

## Quick Start

### Option 1: Windows (Quick Test)
```bash
start_us30_momentum.bat
```

### Option 2: Linux (Production)
```bash
# Install systemd service
sudo cp systemd/us30-momentum-scanner.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable us30-momentum-scanner
sudo systemctl start us30-momentum-scanner

# Check status
sudo systemctl status us30-momentum-scanner
```

### Option 3: Screen Session (Development)
```bash
screen -dmS us30_momentum python main_us30.py
screen -r us30_momentum  # Attach to view
# Ctrl+A, D to detach
```

### Option 4: Start All Scanners
```bash
./start_all_scanners.sh
```

## Configuration

Edit `config/us30_config.json` to adjust:

```json
{
  "us30_strategy": {
    "min_fvg_percent": 0.05,        // Minimum gap size (0.05%)
    "min_adx": 25,                  // Momentum threshold
    "min_volume_ratio": 1.2,        // Volume confirmation
    "min_candle_body_percent": 60,  // Candle strength
    "initial_tp_atr": 2.5,          // Take profit (2.5 ATR)
    "stop_loss_atr": 1.5,           // Stop loss (1.5 ATR)
    "trail_after_atr": 1.5          // Trail after profit
  }
}
```

## What Makes This Different

### OLD Strategy Issues
- Required 5+ confluence factors (too restrictive)
- Take profit only 1.0 ATR (~50-100 points)
- No FVG detection
- No structure break detection
- Missed big moves

### NEW Strategy Advantages
✅ **FVG Detection** - Catches imbalance zones
✅ **Structure Breaks** - BOS (continuation) & CHoCH (reversal)
✅ **Higher Targets** - 2.5 ATR (~250-500 points)
✅ **Trailing Stops** - Locks in profits on big moves
✅ **Simpler Entry** - Only needs 1-2 triggers + confirmation
✅ **Confidence Scoring** - 3-5 star system

## Expected Signals

### Signal Format
```
🚀 LONG Signal - US30 (5m)
Strategy: US30 Momentum
Confidence: ⭐⭐⭐⭐⭐ (5/5)

💰 Entry: 47,184.00
🛑 Stop Loss: 46,984.00
🎯 Take Profit: 47,484.00
📊 Risk/Reward: 1.67

✅ Confluence: Bullish FVG 0.15% | BOS (strength 4/5) | ADX 28.5 | Vol 1.8x | Body 75%
```

### Signal Quality
- **3 stars** ⭐⭐⭐ - Basic setup (FVG or structure)
- **4 stars** ⭐⭐⭐⭐ - Strong setup (FVG + structure)
- **5 stars** ⭐⭐⭐⭐⭐ - Perfect setup (FVG + BOS + high volume)

## Monitoring

### View Logs
```bash
# Real-time log
tail -f logs/us30_momentum_scanner.log

# Last 100 lines
tail -100 logs/us30_momentum_scanner.log

# Search for signals
grep "SIGNAL" logs/us30_momentum_scanner.log
```

### Check Scanner Status
```bash
# Systemd
sudo systemctl status us30-momentum-scanner

# Screen
screen -list | grep us30_momentum

# Process
ps aux | grep main_us30.py
```

### Excel Reports
- File: `logs/us30_momentum_scans.xlsx`
- Updates: Every hour
- Email: Sent to configured address

## Troubleshooting

### Scanner Not Starting
```bash
# Check logs
tail -50 logs/us30_momentum_scanner.log

# Test imports
python -c "from src.us30_strategy import US30Strategy; print('OK')"

# Run test
python test_us30_strategy.py
```

### No Signals Detected
- Check ADX threshold (default: 25)
- Check volume ratio (default: 1.2x)
- Lower thresholds in config for testing
- Verify market is open and volatile

### Too Many Signals
- Increase `min_adx` (try 30)
- Increase `min_volume_ratio` (try 1.5)
- Increase `min_fvg_percent` (try 0.1)

## Performance Tuning

### More Aggressive (More Signals)
```json
{
  "min_adx": 20,
  "min_volume_ratio": 1.0,
  "min_candle_body_percent": 50
}
```

### More Conservative (Fewer, Higher Quality)
```json
{
  "min_adx": 30,
  "min_volume_ratio": 1.5,
  "min_candle_body_percent": 70
}
```

### Bigger Targets (For Big Moves)
```json
{
  "initial_tp_atr": 3.0,
  "stop_loss_atr": 1.5,
  "trail_after_atr": 2.0
}
```

## Next Steps

1. **Start the scanner**: `start_us30_momentum.bat` or systemd
2. **Monitor Telegram**: Watch for signal alerts
3. **Review logs**: Check what's being detected
4. **Adjust config**: Tune based on results
5. **Track performance**: Excel reports show all scans

## Key Differences from Other Scanners

| Feature | US30 Scalp/Swing | US30 Momentum (NEW) |
|---------|------------------|---------------------|
| Entry Logic | EMA crossovers | FVG + Structure breaks |
| Take Profit | 1.0 ATR | 2.5 ATR |
| Risk:Reward | 0.67:1 | 1.67:1 |
| FVG Detection | ❌ | ✅ |
| Structure Breaks | ❌ | ✅ |
| Trailing Stops | ❌ | ✅ |
| Big Move Potential | Low | High |

---

**The new US30 Momentum scanner is specifically designed to catch those R2000 → R22000 moves you showed me!** 🎯

It runs alongside your existing scanners, giving you more coverage and better entries on big momentum moves.
