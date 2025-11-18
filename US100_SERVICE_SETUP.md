# US100 Scanner Service Setup

## Quick Fix (Recommended)

The US100 scanner service wasn't installed during the initial setup. Here's how to fix it:

### On Your Linux Server

```bash
# Navigate to project directory
cd ~/telegramscalperbot

# Run the fix script
sudo bash FIX_US100_SERVICE.sh
```

That's it! The script will:
1. Create the service file with correct paths
2. Install it to systemd
3. Reload systemd

### Start the Service

```bash
# Enable to start on boot
sudo systemctl enable btc-us100-scanner

# Start now
sudo systemctl start btc-us100-scanner

# Check status
sudo systemctl status btc-us100-scanner
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u btc-us100-scanner -f

# Or view log file
tail -f ~/telegramscalperbot/logs/us100_scanner.log
```

---

## Alternative: Manual Installation

If you prefer to do it manually:

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/btc-us100-scanner.service
```

### Step 2: Paste This Content

**Important:** Replace `/home/predeshen/telegramscalperbot` with your actual path!

```ini
[Unit]
Description=US100/NASDAQ Trading Scanner
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=predeshen
Group=predeshen
WorkingDirectory=/home/predeshen/telegramscalperbot
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /home/predeshen/telegramscalperbot/main_us100.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=us100-scanner

# Resource limits
MemoryLimit=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

### Step 3: Reload and Start

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable btc-us100-scanner

# Start service
sudo systemctl start btc-us100-scanner

# Check status
sudo systemctl status btc-us100-scanner
```

---

## Verify Installation

### Check Service Status

```bash
sudo systemctl status btc-us100-scanner
```

**Expected output:**
```
● btc-us100-scanner.service - US100/NASDAQ Trading Scanner
     Loaded: loaded (/etc/systemd/system/btc-us100-scanner.service; enabled)
     Active: active (running) since ...
```

### Check Logs

```bash
# Last 50 lines
sudo journalctl -u btc-us100-scanner -n 50

# Real-time
sudo journalctl -u btc-us100-scanner -f
```

**Expected log output:**
```
[INFO] US100/NASDAQ Scanner Started
[INFO] Diagnostic system initialized
[INFO] Configuration loaded
[INFO] Successfully connected for US100
[INFO] Starting main polling loop...
```

### Check Telegram

You should receive a startup message in Telegram:
```
🚀 US100/NASDAQ Scanner Started

💰 Current Price: $15,500.00
⏰ Timeframes: 1m, 5m, 15m, 1h, 4h
🎯 Strategy: FVG + Structure Breaks
📊 Min ADX: 25
🎯 Target: 2.5 ATR

🔍 Hunting for big moves...
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check detailed error
sudo journalctl -u btc-us100-scanner -xe

# Common issues:
```

**1. Python not found:**
```bash
# Check Python installation
which python3
python3 --version

# If not found, install:
sudo apt update
sudo apt install python3 python3-pip
```

**2. Missing dependencies:**
```bash
cd ~/telegramscalperbot
pip3 install -r requirements.txt
```

**3. File not found:**
```bash
# Check if main_us100.py exists
ls -la ~/telegramscalperbot/main_us100.py

# If missing, you need to pull latest code
```

**4. Permission denied:**
```bash
# Fix permissions
cd ~/telegramscalperbot
chmod +x main_us100.py
chown -R predeshen:predeshen .
```

**5. Telegram credentials missing:**
```bash
# Check .env file
cat ~/telegramscalperbot/.env

# Should contain:
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_CHAT_ID=your_chat_id
```

### Service Starts But No Signals

```bash
# Check if scanner is running
sudo systemctl status btc-us100-scanner

# View logs for errors
sudo journalctl -u btc-us100-scanner -n 100

# Check diagnostic output
# (Wait for 18:00 UTC for daily report in Telegram)
```

### Test Scanner Manually

Before running as service, test manually:

```bash
cd ~/telegramscalperbot
python3 main_us100.py
```

Press Ctrl+C to stop. If it runs without errors, the service should work.

---

## Managing the Service

### Start/Stop/Restart

```bash
# Start
sudo systemctl start btc-us100-scanner

# Stop
sudo systemctl stop btc-us100-scanner

# Restart
sudo systemctl restart btc-us100-scanner

# Status
sudo systemctl status btc-us100-scanner
```

### Enable/Disable Auto-Start

```bash
# Enable (start on boot)
sudo systemctl enable btc-us100-scanner

# Disable (don't start on boot)
sudo systemctl disable btc-us100-scanner

# Check if enabled
systemctl is-enabled btc-us100-scanner
```

### View Logs

```bash
# Last 50 lines
sudo journalctl -u btc-us100-scanner -n 50

# Real-time (follow)
sudo journalctl -u btc-us100-scanner -f

# Today's logs
sudo journalctl -u btc-us100-scanner --since today

# Last hour
sudo journalctl -u btc-us100-scanner --since "1 hour ago"
```

---

## All Scanner Services

After installing US100, you have these services:

### Legacy Single-Symbol Scanners
```bash
btc-scalp-scanner          # BTC 1m/5m/15m
btc-swing-scanner          # BTC 15m/1h/4h/1d
gold-scalp-scanner         # XAUUSD 1m/5m/15m
gold-swing-scanner         # XAUUSD 15m/1h/4h/1d
us30-scalp-scanner         # US30 1m/5m/15m
us30-swing-scanner         # US30 15m/1h/4h/1d
us30-momentum-scanner      # US30 momentum strategy
btc-us100-scanner          # US100/NASDAQ (NEW!)
```

### Multi-Symbol Scanners (Recommended)
```bash
multi-crypto-scalp-scanner # BTC, ETH, SOL (1m/5m/15m)
multi-crypto-swing-scanner # BTC, ETH (15m/1h/4h/1d)
multi-fx-scalp-scanner     # EUR/USD, GBP/USD (5m/15m/1h)
multi-mixed-scanner        # BTC, ETH, EUR/USD (15m/1h/4h)
```

### Start Multiple Scanners

```bash
# Start all legacy scanners
sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner

# Start all multi-symbol scanners
sudo systemctl start multi-*-scanner

# Start specific combination
sudo systemctl start btc-us100-scanner us30-momentum-scanner multi-crypto-scalp-scanner

# Check status of all
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner multi-*-scanner
```

---

## Configuration

The US100 scanner uses: `config/us100_config.json`

### Key Settings

```json
{
  "signal_rules": {
    "volume_spike_threshold": 1.5,
    "rsi_min": 30,
    "rsi_max": 70,
    "adx_min_trend_alignment": 20
  },
  "quality_filter": {
    "min_confluence_factors": 3,
    "min_confidence_score": 3,
    "min_risk_reward": 1.2
  },
  "us100_strategy": {
    "h4_hvg": {
      "enabled": true,
      "min_fvg_percent": 0.05,
      "min_adx": 25,
      "timeframes": ["4h", "1h"]
    },
    "momentum_breakout": {
      "enabled": true,
      "min_volume_spike": 2.0,
      "min_price_move_percent": 0.5,
      "timeframes": ["1m", "5m", "15m"]
    }
  }
}
```

### Adjust Signal Frequency

**More signals:**
```json
"min_confluence_factors": 2,  // Was 3
"min_confidence_score": 2      // Was 3
```

**Fewer, higher quality signals:**
```json
"min_confluence_factors": 4,  // Was 3
"min_confidence_score": 4      // Was 3
```

After editing config:
```bash
sudo systemctl restart btc-us100-scanner
```

---

## Expected Behavior

### Startup
- Scanner connects to data source
- Loads historical data
- Sends startup message to Telegram
- Begins scanning every 60 seconds

### Signal Generation
- 3-7 signals per day (varies with market conditions)
- Each signal includes entry, stop loss, take profit
- Confidence score 3-5/5
- Minimum 3 confluence factors

### Daily Reports
- Sent at 18:00 UTC
- Shows detection attempts, successes, rejections
- Provides recommendations

### No-Signal Alerts
- If no signals for 4+ hours
- Includes diagnostic information
- Helps identify issues

---

## Success Checklist

- [ ] Service file installed
- [ ] Service enabled
- [ ] Service running
- [ ] No errors in logs
- [ ] Startup message received in Telegram
- [ ] Scanner polling every 60 seconds
- [ ] Waiting for first signal

---

## Need Help?

1. **Check logs:** `sudo journalctl -u btc-us100-scanner -f`
2. **Test manually:** `python3 main_us100.py`
3. **Review config:** `cat config/us100_config.json`
4. **Check Telegram:** Verify bot token and chat ID in .env

---

**Your US100 scanner is ready to hunt for NASDAQ signals! 🚀**
