# Quick Start Guide

## 🚀 Get Your Scanners Running in 5 Minutes

---

## Prerequisites

✅ Python 3.9+ installed  
✅ Git repository cloned  
✅ Telegram bot token and chat ID

---

## Step 1: Install Dependencies (1 minute)

```bash
# Install Python packages
pip install -r requirements.txt
```

---

## Step 2: Configure Telegram (1 minute)

```bash
# Create .env file
nano .env
```

Add your credentials:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Get Telegram Credentials:**
1. Create bot: Talk to @BotFather on Telegram
2. Get chat ID: Talk to @userinfobot on Telegram

---

## Step 3: Test the System (1 minute)

```bash
# Run comprehensive test
python test_comprehensive_system.py
```

**Expected Output:**
```
🎉 ALL TESTS PASSED!
✅ Signal detection system is ready for deployment
```

---

## Step 4: Start a Scanner (1 minute)

### Option A: Run Directly (Testing)

```bash
# BTC Scalp Scanner
python main.py

# BTC Swing Scanner
python main_swing.py

# US30 Momentum Scanner
python main_us30.py

# US100/NASDAQ Scanner
python main_us100.py

# Multi-Symbol Scanner
python main_multi_symbol.py --config config/multi_crypto_scalp.json
```

### Option B: Install as Service (Production)

```bash
# Install all services
sudo bash deployment/install_services.sh

# Start specific scanner
sudo systemctl start btc-us100-scanner
sudo systemctl enable btc-us100-scanner

# Check status
sudo systemctl status btc-us100-scanner
```

---

## Step 5: Monitor Signals (1 minute)

### View Logs
```bash
# Real-time logs
tail -f logs/btc_scalp.log

# Or for services
sudo journalctl -u btc-us100-scanner -f
```

### Check Telegram
- You'll receive signal alerts in your Telegram chat
- Daily diagnostic reports at 18:00 UTC
- No-signal alerts if 4+ hours without signals

---

## 🎯 What to Expect

### Signal Alerts
You'll receive messages like:
```
🚨 BTC/USD Signal 🚨

📊 Symbol: BTC/USD
⏰ Timeframe: 5m
📈 Type: LONG
🎯 Strategy: EMA Crossover

💰 Entry: $45,000.00
🛑 Stop Loss: $44,500.00
🎯 Take Profit: $46,000.00

📊 Confidence: 4/5
✅ Factors: 5/7
🔍 Met: volume_spike, rsi_favorable, ema_alignment...

⏰ Time: 14:23:45
```

### Daily Reports (18:00 UTC)
```
📊 Daily Diagnostic Summary

Scanner: BTC-Scalp
Period: Last 24 hours

📈 Detection Attempts: 145
✅ Successful Signals: 8
❌ Filter Rejections: 137

Top Rejection Reasons:
  • Low confluence (45%)
  • Duplicate signal (28%)
  • Low confidence (18%)

💡 Recommendations:
  • Consider relaxing min_confluence_factors
  • Review duplicate detection window
```

---

## 🔧 Quick Configuration Adjustments

### Make Signals More Frequent
Edit `config/config.json`:
```json
{
  "quality_filter": {
    "min_confluence_factors": 2,  // Was 3
    "min_confidence_score": 2,     // Was 3
    "min_risk_reward": 1.0         // Was 1.2
  }
}
```

### Make Signals More Selective
```json
{
  "quality_filter": {
    "min_confluence_factors": 4,  // Was 3
    "min_confidence_score": 4,     // Was 3
    "min_risk_reward": 1.5         // Was 1.2
  }
}
```

### Enable Bypass Mode (Testing Only)
```json
{
  "bypass_mode": {
    "enabled": true,              // Disables quality filters
    "auto_disable_after_hours": 2 // Auto-disable after 2 hours
  }
}
```

---

## 🎯 Scanner Comparison

### BTC Scalp Scanner (main.py)
- **Timeframes:** 1m, 5m, 15m
- **Best for:** Quick scalp trades
- **Signals per day:** 5-10
- **Config:** config/config.json

### BTC Swing Scanner (main_swing.py)
- **Timeframes:** 15m, 1h, 4h, 1d
- **Best for:** Swing trades
- **Signals per day:** 2-5
- **Config:** config/config_multitime.json

### US30 Momentum Scanner (main_us30.py)
- **Timeframes:** 1m, 5m, 15m, 1h
- **Best for:** US30 momentum trades
- **Signals per day:** 3-8
- **Config:** config/us30_config.json

### US100/NASDAQ Scanner (main_us100.py)
- **Timeframes:** 1m, 5m, 15m, 1h, 4h
- **Best for:** NASDAQ momentum + H4-HVG
- **Signals per day:** 3-7
- **Config:** config/us100_config.json

### Multi-Symbol Scanner (main_multi_symbol.py)
- **Symbols:** BTC, ETH, SOL, EUR/USD, GBP/USD
- **Best for:** Diversified scanning
- **Signals per day:** 10-20 (across all symbols)
- **Configs:** 
  - config/multi_crypto_scalp.json
  - config/multi_crypto_swing.json
  - config/multi_fx_scalp.json
  - config/multi_mixed.json

---

## 🚨 Troubleshooting

### No Signals Generated
```bash
# Check diagnostic report
# (Sent daily at 18:00 UTC to Telegram)

# Or check logs
tail -f logs/btc_scalp.log | grep "rejection"

# Enable bypass mode temporarily
# Edit config.json: "bypass_mode": {"enabled": true}
```

### Scanner Won't Start
```bash
# Check dependencies
pip install -r requirements.txt

# Check configuration
python -c "import json; json.load(open('config/config.json'))"

# Check Telegram credentials
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### Too Many Signals
```bash
# Increase quality thresholds in config.json
# min_confluence_factors: 3 → 4
# min_confidence_score: 3 → 4
```

### Service Won't Start
```bash
# Check service status
sudo systemctl status btc-us100-scanner

# View service logs
sudo journalctl -u btc-us100-scanner -n 50

# Restart service
sudo systemctl restart btc-us100-scanner
```

---

## 📊 Monitoring Commands

```bash
# Check all scanner services
sudo systemctl status btc-*-scanner us30-*-scanner multi-*-scanner

# View logs for all scanners
tail -f logs/*.log

# Check signal generation rate
grep "Signal detected" logs/btc_scalp.log | wc -l

# Check filter rejections
grep "rejected" logs/btc_scalp.log | tail -20
```

---

## 🎯 Next Steps

1. **Run for 24 hours** - Let the scanner run and collect data
2. **Review diagnostic reports** - Check Telegram at 18:00 UTC
3. **Adjust thresholds** - Based on signal frequency
4. **Enable more scanners** - Start additional scanners as needed
5. **Monitor performance** - Track signal quality and profitability

---

## 📞 Need Help?

1. **Check logs:** `tail -f logs/*.log`
2. **Review diagnostics:** Wait for 18:00 UTC report
3. **Test system:** `python test_comprehensive_system.py`
4. **Read docs:** See FINAL_IMPLEMENTATION_SUMMARY.md

---

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] Telegram configured
- [ ] Tests passing
- [ ] Scanner running
- [ ] Receiving alerts
- [ ] Logs accessible
- [ ] Diagnostic reports arriving

---

**You're all set! Your trading scanners are now running and monitoring the markets 24/7.**

🎉 Happy Trading!
