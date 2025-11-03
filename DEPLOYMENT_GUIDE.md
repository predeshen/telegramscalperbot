# Complete Scanner Deployment Guide

## Quick Start (All Scanners)

### 1. Make Scripts Executable
```bash
chmod +x start_all_scanners.sh
chmod +x stop_all_scanners.sh
```

### 2. Start All Scanners
```bash
# Start all with health monitoring
./start_all_scanners.sh --monitor

# Or without monitoring
./start_all_scanners.sh
```

### 3. Check Status
```bash
screen -list
# Should show: btc_scanner, btc_swing, (xau_scanner when ready)
```

## What Gets Started

### 1. BTC Scalping Scanner
- **Timeframes**: 1m, 5m
- **Purpose**: Quick scalps
- **Signals/day**: 2-10
- **Screen**: `btc_scanner`
- **Log**: `logs/scanner.log`

### 2. BTC Swing Scanner  
- **Timeframes**: 15m, 1h, 4h, 1d
- **Purpose**: Longer holds
- **Signals/day**: 1-3
- **Screen**: `btc_swing`
- **Log**: `logs/scanner_swing.log`

### 3. XAU/USD Gold Scanner (Coming Soon)
- **Timeframes**: 1m, 5m
- **Purpose**: Gold scalping
- **Features**: Session-aware, news pause, spread monitoring
- **Screen**: `xau_scanner`
- **Log**: `logs/scanner_gold.log`

## Telegram Notifications

You'll receive notifications for:

### Scanner Lifecycle
- ✅ **Scanner Started** - When each scanner begins
- 🛑 **Scanner Stopped** - If scanner stops unexpectedly (with --monitor)
- 📊 **Deployment Complete** - Summary when all start

### Trading Signals
- 🚨 **New Signal** - Entry, SL, TP with detailed reasoning
- 📈 **Breakeven** - When price reaches 50% to target
- 🎯 **Target Approach** - When within 10% of TP
- ⚠️ **Stop Warning** - When within 10% of SL

### Gold-Specific (XAU/USD)
- 🌏 **Session Change** - Asian → London → NY
- 📰 **News Pause** - 30 min before high-impact news
- ✅ **Trading Resumed** - After news event
- 📊 **Spread Warning** - When spread > 15 pips

## Health Monitoring

### Automatic (with --monitor flag)
```bash
./start_all_scanners.sh --monitor
```

Checks every 5 minutes:
- If scanner stopped → Telegram alert
- Runs in background screen: `scanner_monitor`

### Manual Checks
```bash
# View all screens
screen -list

# Check specific scanner
screen -r btc_scanner  # Ctrl+A, D to detach

# View logs
tail -f logs/scanner.log
tail -f logs/scanner_swing.log
```

## Managing Scanners

### View Running Scanners
```bash
screen -list
```

### Attach to Scanner
```bash
screen -r btc_scanner    # BTC scalping
screen -r btc_swing      # BTC swing
screen -r xau_scanner    # Gold (when ready)

# Detach: Ctrl+A, then D
```

### Stop All Scanners
```bash
./stop_all_scanners.sh
```

### Stop Individual Scanner
```bash
screen -X -S btc_scanner quit
screen -X -S btc_swing quit
screen -X -S xau_scanner quit
```

### Restart Scanner
```bash
# Stop
screen -X -S btc_scanner quit

# Start
screen -dmS btc_scanner python main.py
```

## Logs

### View Real-Time
```bash
tail -f logs/scanner.log          # BTC scalping
tail -f logs/scanner_swing.log    # BTC swing
tail -f logs/scanner_gold.log     # Gold
```

### Search Logs
```bash
# Find signals
grep "SIGNAL" logs/scanner.log

# Find errors
grep "ERROR" logs/scanner.log

# Last 100 lines
tail -100 logs/scanner.log
```

## Troubleshooting

### Scanner Won't Start
```bash
# Check Python
python --version

# Test manually
python main.py
python main_swing.py

# Check environment
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### No Telegram Notifications
```bash
# Verify .env file
cat .env

# Should contain:
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_CHAT_ID=your_chat_id

# Test Telegram
python -c "from src.alerter import TelegramAlerter; import os; a = TelegramAlerter(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID')); print('Testing...'); a.send_message('Test from scanner')"
```

### Scanner Keeps Stopping
```bash
# Check logs for errors
tail -100 logs/scanner.log

# Check system resources
free -h
df -h

# Restart with monitoring
./stop_all_scanners.sh
./start_all_scanners.sh --monitor
```

### No Signals
This is NORMAL! The scanners wait for high-probability setups.

Check current market conditions:
```bash
python verify_data.py
```

## Configuration

### BTC Scalping
Edit `config/config.json`:
- Timeframes: 1m, 5m
- Polling: 10 seconds
- Stop loss: 1.5x ATR
- Take profit: 1.0x ATR

### BTC Swing
Edit `config/config_multitime.json`:
- Timeframes: 15m, 1h, 4h, 1d
- Polling: 60 seconds
- Stop loss: 2.0x ATR
- Take profit: 1.5x ATR

### XAU/USD Gold
Edit `xauusd_scanner/config_gold.json`:
- Timeframes: 1m, 5m
- Session-aware trading
- News calendar integration
- Spread monitoring

## Best Practices

### 1. Run on Dedicated Server
- Linux VPS recommended
- Stable internet connection
- 24/7 uptime

### 2. Monitor Regularly
- Check Telegram daily
- Review logs weekly
- Update news calendar weekly (Gold)

### 3. Backup Configuration
```bash
# Backup configs
cp config/config.json config/config.json.backup
cp config/config_multitime.json config/config_multitime.json.backup
cp xauusd_scanner/config_gold.json xauusd_scanner/config_gold.json.backup
```

### 4. Update News Events (Gold)
```bash
# Every Sunday
python -m xauusd_scanner.news_updater weekly
python -m xauusd_scanner.news_updater list 7
```

### 5. Clean Up Old Data
```bash
# Monthly
python -m xauusd_scanner.news_updater cleanup
find logs/ -name "*.log" -mtime +30 -delete
```

## Performance Expectations

### BTC Scalping (1m/5m)
- Signals: 2-10 per day
- Hold time: Minutes to hours
- Win rate: 60-70%
- R:R: 0.67:1

### BTC Swing (15m/1h/4h/1d)
- Signals: 1-3 per day
- Hold time: Hours to days
- Win rate: 60-70%
- R:R: 0.75:1

### XAU/USD Gold (1m/5m)
- Signals: 3-8 per session
- Hold time: Minutes to hours
- Win rate: 65-75%
- R:R: 1.25:1
- Best sessions: London, NY Overlap

## Support

### Check Status
```bash
# All scanners
screen -list

# Logs
ls -lh logs/

# Processes
ps aux | grep python
```

### Get Help
1. Check logs first
2. Review this guide
3. Test with `verify_data.py`
4. Check GitHub issues

## Quick Reference

```bash
# Start everything
./start_all_scanners.sh --monitor

# Stop everything
./stop_all_scanners.sh

# View scanner
screen -r btc_scanner

# View logs
tail -f logs/scanner.log

# Check data
python verify_data.py

# Update news (Gold)
python -m xauusd_scanner.news_updater weekly
```

## Next Steps

1. ✅ Deploy scanners
2. ✅ Verify Telegram working
3. ⏳ Wait for signals (be patient!)
4. 📊 Review performance weekly
5. 🔧 Adjust configs as needed

Happy trading! 🚀
