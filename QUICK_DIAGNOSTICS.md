# Quick Diagnostics - Run These Commands

## 1. Check .env File

```bash
cat .env
```

**Look for:**
- `TELEGRAM_CHAT_ID=` should have YOUR chat ID (not "your_chat_id_here")
- If it's wrong, fix it: `nano .env`

## 2. Check Running Services

```bash
# Check which are running
systemctl is-active btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner
```

## 3. View Logs for Working Scanners

```bash
# BTC Scalp (should be working)
tail -n 50 logs/scanner.log

# Look for:
# - "Scanner is now running"
# - "Telegram message sent successfully"
# - Any error messages
```

## 4. Check Why US30 Scanners Are Failing

```bash
# Check US30 scalp error
sudo journalctl -u us30-scalp-scanner -n 50 --no-pager

# Check US30 swing error
sudo journalctl -u us30-swing-scanner -n 50 --no-pager
```

## 5. Fix US30 Scanners (if files missing)

```bash
# Check if US30 scanner files exist
ls -la us30_scanner/

# If missing, they might not be in the repo
# For now, disable them:
sudo systemctl stop us30-scalp-scanner us30-swing-scanner
sudo systemctl disable us30-scalp-scanner us30-swing-scanner
```

## 6. Test Telegram Manually

```bash
# Test if Telegram credentials work
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

print(f"Bot Token: {bot_token[:20]}..." if bot_token else "Bot Token: NOT SET")
print(f"Chat ID: {chat_id}")

if bot_token and chat_id and chat_id != "your_chat_id_here":
    import requests
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": "✅ Test message from scanner!"}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("✅ Telegram message sent successfully!")
    else:
        print(f"❌ Failed: {response.text}")
else:
    print("❌ Telegram credentials not configured properly")
EOF
```

## 7. Restart Working Services

```bash
# Restart the 4 working services
sudo systemctl restart btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner

# Check status
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner
```

## 8. Monitor Logs Live

```bash
# Watch all logs in real-time
tail -f logs/*.log
```

---

## Most Likely Issues

### Issue 1: Telegram Chat ID Not Set

**Check:**
```bash
grep TELEGRAM_CHAT_ID .env
```

**Should show:** `TELEGRAM_CHAT_ID=123456789` (your actual ID)

**If wrong:**
```bash
nano .env
# Change the chat ID
# Save: Ctrl+O, Enter, Ctrl+X

# Restart services
sudo systemctl restart btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner
```

### Issue 2: US30 Scanner Files Missing

**Check:**
```bash
ls us30_scanner/
```

**If missing main_us30_scalp.py or main_us30_swing.py:**
```bash
# Disable these services for now
sudo systemctl stop us30-scalp-scanner us30-swing-scanner
sudo systemctl disable us30-scalp-scanner us30-swing-scanner
```

### Issue 3: Telegram Not Sending

**After fixing .env, restart:**
```bash
sudo systemctl restart btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner

# Watch logs
tail -f logs/scanner.log
```

---

## Expected Output When Working

**Logs should show:**
```
[INFO] BTC Scalping Scanner Starting
[INFO] Successfully connected to binance
[INFO] Loaded 1m data with indicators
[INFO] Telegram message sent successfully
[INFO] Scanner is now running
```

**Telegram should receive:**
```
🟢 BTC Scalping Scanner Started

💰 Current Price: $107,xxx
📊 Timeframes: 1m, 5m
🔍 Scanning for opportunities...
```

---

Run these commands in order and let me know what you find!
