# Quick Start Guide

Get your BTC Scalping Scanner running in 5 minutes!

## Prerequisites

- Linux VM (Ubuntu/Debian)
- Python 3.9+
- Root/sudo access

## Installation (3 steps)

### 1. Install

```bash
# Clone or copy the project to your VM
cd btc-scalping-scanner

# Run installation script
sudo bash deployment/install.sh
```

### 2. Configure

```bash
# Edit configuration
sudo nano /etc/btc-scanner/config.json
```

**Update these fields:**

```json
{
  "smtp": {
    "password": "YOUR_SMTP_PASSWORD"
  },
  "telegram": {
    "enabled": true,
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  }
}
```

**To get Telegram credentials:**
1. Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy token
2. Talk to [@userinfobot](https://t.me/userinfobot) → copy chat ID

### 3. Start

```bash
# Enable and start service
sudo systemctl enable btc-scanner
sudo systemctl start btc-scanner

# Check it's running
sudo systemctl status btc-scanner
```

## View Logs

```bash
# Live logs
sudo journalctl -u btc-scanner -f

# Or application log
sudo tail -f /var/log/btc-scanner/scanner.log
```

## What to Expect

- **Startup**: ~10 seconds to connect and load data
- **Signals**: Varies by market conditions (could be 0-10 per day)
- **Alerts**: Email + Telegram (if enabled) within 3 seconds of detection

## Example Signal

You'll receive alerts like this:

```
🟢 BTC/USD LONG Signal

Entry: $65,432.50
Stop Loss: $65,200.00 (-0.36%)
Take Profit: $65,665.00 (+0.36%)
R:R: 1:1.00

Market: BULLISH | TF: 5m
ATR: $232.50 | Confidence: 5/5
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u btc-scanner -n 50

# Verify config
python3 -c "import json; json.load(open('/etc/btc-scanner/config.json'))"
```

### No signals
- Normal! Signals require specific market conditions
- Check logs show "WebSocket connection established"
- Verify "Loaded 1m data" and "Loaded 5m data" in logs

### Email fails
```bash
# Test SMTP
python3 -c "
import smtplib
server = smtplib.SMTP_SSL('mail.hashub.co.za', 465, timeout=10)
server.login('alerts@hashub.co.za', 'YOUR_PASSWORD')
print('✓ SMTP works')
server.quit()
"
```

### Telegram fails
- Verify bot token and chat ID are correct
- Send `/start` to your bot first
- Check `pip3 list | grep telegram` shows `python-telegram-bot`

## Commands Cheat Sheet

```bash
# Start
sudo systemctl start btc-scanner

# Stop
sudo systemctl stop btc-scanner

# Restart (after config changes)
sudo systemctl restart btc-scanner

# Status
sudo systemctl status btc-scanner

# Logs (live)
sudo journalctl -u btc-scanner -f

# Logs (last 100 lines)
sudo journalctl -u btc-scanner -n 100
```

## Testing Locally (Development)

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run directly
python3 main.py

# Run tests
pytest tests/
```

## Next Steps

- Monitor for 24 hours to verify stability
- Adjust signal rules in config if needed
- Check logs daily for errors
- Review signal quality and adjust parameters

## Support

- Check README.md for full documentation
- Review logs for detailed error messages
- Test components individually (SMTP, Telegram, exchange connection)

---

**Ready to trade?** Remember: This is a signal detection tool. Always verify signals manually and use proper risk management!
