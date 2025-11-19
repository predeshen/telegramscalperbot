# Installation and Startup Guide

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd ~/telegramscalperbot
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install Services
```bash
sudo bash deployment/install_services.sh
```

### 4. Start All Scanners
```bash
sudo bash deployment/start_all_scanners.sh
```

### 5. Verify Status
```bash
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

---

## Detailed Installation Steps

### Step 1: System Preparation

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required system packages
sudo apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  git \
  curl \
  wget \
  systemd
```

### Step 2: Clone/Update Repository

```bash
# If first time
git clone https://github.com/predeshen/telegramscalperbot.git
cd telegramscalperbot

# If already cloned
cd ~/telegramscalperbot
git pull origin main
```

### Step 3: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create `.env` file in project root:

```bash
cat > .env << 'EOF'
# Data Provider Credentials
ALPHA_VANTAGE_KEY=66IUJDWBSTV9U220
TWELVE_DATA_KEY=a4f7101c037f4cf5949a1be62973283f

# Email Configuration
SMTP_PASSWORD=Password@2025#!

# Telegram Configuration
TELEGRAM_BOT_TOKEN=8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M
TELEGRAM_CHAT_ID=8119046376

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF

# Secure the file
chmod 600 .env
```

### Step 5: Create Scanner User (Optional but Recommended)

```bash
# Create dedicated scanner user
sudo useradd -m -s /bin/bash scanner

# Create directories
sudo mkdir -p /opt/trading-scanners
sudo mkdir -p /etc/trading-scanners
sudo mkdir -p /var/log/trading-scanners

# Copy project
sudo cp -r ~/telegramscalperbot/* /opt/trading-scanners/

# Set permissions
sudo chown -R scanner:scanner /opt/trading-scanners
sudo chown -R scanner:scanner /var/log/trading-scanners
sudo chmod 755 /opt/trading-scanners
sudo chmod 755 /var/log/trading-scanners
```

### Step 6: Install Systemd Services

```bash
# Copy service files
sudo cp deployment/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable btc-scalp-scanner
sudo systemctl enable btc-swing-scanner
sudo systemctl enable gold-scalp-scanner
sudo systemctl enable gold-swing-scanner
sudo systemctl enable us30-scalp-scanner
sudo systemctl enable us30-swing-scanner
sudo systemctl enable us100-scanner
sudo systemctl enable multi-crypto-scanner
```

---

## Starting the Scanners

### Option 1: Start All Scanners at Once

```bash
sudo bash deployment/start_all_scanners.sh
```

Output:
```
Starting all trading scanners...
✓ BTC Scalp Scanner started
✓ BTC Swing Scanner started
✓ Gold Scalp Scanner started
✓ Gold Swing Scanner started
✓ US30 Scalp Scanner started
✓ US30 Swing Scanner started
✓ US100 Scanner started
✓ Multi-Crypto Scanner started
All scanners started successfully!
```

### Option 2: Start Individual Scanners

```bash
# BTC Scalp (1m, 5m, 15m)
sudo systemctl start btc-scalp-scanner

# BTC Swing (15m, 1h, 4h, 1d)
sudo systemctl start btc-swing-scanner

# Gold Scalp (1m, 5m, 15m)
sudo systemctl start gold-scalp-scanner

# Gold Swing (15m, 1h, 4h, 1d)
sudo systemctl start gold-swing-scanner

# US30 Scalp (1m, 5m, 15m)
sudo systemctl start us30-scalp-scanner

# US30 Swing (15m, 1h, 4h)
sudo systemctl start us30-swing-scanner

# US100 (1m, 5m, 15m, 4h)
sudo systemctl start us100-scanner

# Multi-Crypto (BTC, ETH, SOL)
sudo systemctl start multi-crypto-scanner
```

### Option 3: Start with Manual Python

```bash
# Activate venv
source venv/bin/activate

# Run specific scanner
python3 main.py                    # BTC Scalp
python3 main_swing.py              # BTC Swing
python3 xauusd_scanner/main_gold.py # Gold Scalp
python3 main_us30.py               # US30
python3 main_us100.py              # US100
```

---

## Monitoring and Management

### Check Scanner Status

```bash
# Check all scanners
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner

# Check specific scanner
sudo systemctl status btc-scalp-scanner

# Check if running
sudo systemctl is-active btc-scalp-scanner
```

### View Logs

```bash
# View real-time logs
sudo journalctl -u btc-scalp-scanner -f

# View last 100 lines
sudo journalctl -u btc-scalp-scanner -n 100

# View logs from last hour
sudo journalctl -u btc-scalp-scanner --since "1 hour ago"

# View all scanner logs
sudo journalctl -u btc-scalp-scanner -u btc-swing-scanner -u gold-scalp-scanner -f
```

### Restart Scanners

```bash
# Restart all
sudo bash deployment/restart_all_scanners.sh

# Restart specific
sudo systemctl restart btc-scalp-scanner

# Restart and check status
sudo systemctl restart btc-scalp-scanner && sudo systemctl status btc-scalp-scanner
```

### Stop Scanners

```bash
# Stop all
sudo bash deployment/stop_all_scanners.sh

# Stop specific
sudo systemctl stop btc-scalp-scanner

# Stop and disable (won't start on boot)
sudo systemctl stop btc-scalp-scanner
sudo systemctl disable btc-scalp-scanner
```

---

## Configuration

### Update Configuration

Edit the unified config file:

```bash
# Edit config
nano config/unified_config.json

# Or with sudo if in /etc
sudo nano /etc/trading-scanners/config/unified_config.json

# Restart scanners to apply changes
sudo bash deployment/restart_all_scanners.sh
```

### Environment Variables

Set environment variables for sensitive data:

```bash
# Add to ~/.bashrc or ~/.profile
export ALPHA_VANTAGE_KEY="your_key"
export TWELVE_DATA_KEY="your_key"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
export SMTP_PASSWORD="your_password"

# Reload
source ~/.bashrc
```

### Verify Configuration

```bash
# Test config loading
python3 -c "from src.config_loader_unified import get_config; config = get_config(); config.print_summary()"
```

---

## Troubleshooting

### Scanner Won't Start

```bash
# Check service file
sudo systemctl status btc-scalp-scanner

# Check logs
sudo journalctl -u btc-scalp-scanner -n 50

# Check if port is in use
sudo lsof -i :8000

# Check Python path
which python3
python3 --version

# Test manual run
source venv/bin/activate
python3 main.py
```

### No Signals Detected

```bash
# Check config is valid
python3 -c "from src.config_loader_unified import get_config; config = get_config(); is_valid, errors = config.validate(); print('Valid' if is_valid else f'Errors: {errors}')"

# Check data provider credentials
grep -A 5 "credentials" config/unified_config.json

# Check logs for data fetch errors
sudo journalctl -u btc-scalp-scanner | grep -i "error\|failed"
```

### Email Alerts Not Sending

```bash
# Test SMTP connection
telnet mail.hashub.co.za 465

# Check SMTP config
grep -A 10 "smtp" config/unified_config.json

# Check logs for SMTP errors
sudo journalctl -u btc-scalp-scanner | grep -i "smtp\|email"
```

### Telegram Alerts Not Sending

```bash
# Verify bot token
grep "bot_token" config/unified_config.json

# Check logs for Telegram errors
sudo journalctl -u btc-scalp-scanner | grep -i "telegram"

# Test bot token (replace with actual token)
curl -X GET "https://api.telegram.org/bot8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M/getMe"
```

### High Memory Usage

```bash
# Check memory usage
ps aux | grep python3

# Check for memory leaks
sudo journalctl -u btc-scalp-scanner | grep -i "memory"

# Restart scanner
sudo systemctl restart btc-scalp-scanner
```

---

## Service Files Overview

### BTC Scalp Scanner
- **File**: `deployment/btc-scalp-scanner.service`
- **Symbol**: BTC/USD
- **Timeframes**: 1m, 5m, 15m
- **Script**: `main.py`

### BTC Swing Scanner
- **File**: `deployment/btc-swing-scanner.service`
- **Symbol**: BTC/USD
- **Timeframes**: 15m, 1h, 4h, 1d
- **Script**: `main_swing.py`

### Gold Scalp Scanner
- **File**: `deployment/gold-scalp-scanner.service`
- **Symbol**: XAU/USD
- **Timeframes**: 1m, 5m, 15m
- **Script**: `xauusd_scanner/main_gold.py`

### Gold Swing Scanner
- **File**: `deployment/gold-swing-scanner.service`
- **Symbol**: XAU/USD
- **Timeframes**: 15m, 1h, 4h, 1d
- **Script**: `xauusd_scanner/main_gold_swing.py`

### US30 Scalp Scanner
- **File**: `deployment/us30-scalp-scanner.service`
- **Symbol**: ^DJI
- **Timeframes**: 1m, 5m, 15m
- **Script**: `main_us30.py`

### US30 Swing Scanner
- **File**: `deployment/us30-swing-scanner.service`
- **Symbol**: ^DJI
- **Timeframes**: 15m, 1h, 4h
- **Script**: `main_us30.py`

### US100 Scanner
- **File**: `deployment/us100-scanner.service`
- **Symbol**: ^NDX
- **Timeframes**: 1m, 5m, 15m, 4h
- **Script**: `main_us100.py`

### Multi-Crypto Scanner
- **File**: `deployment/multi-crypto-scanner.service`
- **Symbols**: BTC, ETH, SOL
- **Timeframes**: 1m, 5m, 15m
- **Script**: `main_multi_symbol.py`

---

## Health Check Script

Create a health check script:

```bash
cat > check_scanners.sh << 'EOF'
#!/bin/bash

echo "=== Trading Scanner Health Check ==="
echo ""

scanners=(
  "btc-scalp-scanner"
  "btc-swing-scanner"
  "gold-scalp-scanner"
  "gold-swing-scanner"
  "us30-scalp-scanner"
  "us30-swing-scanner"
  "us100-scanner"
  "multi-crypto-scanner"
)

for scanner in "${scanners[@]}"; do
  status=$(sudo systemctl is-active $scanner)
  if [ "$status" = "active" ]; then
    echo "✓ $scanner: RUNNING"
  else
    echo "✗ $scanner: STOPPED"
  fi
done

echo ""
echo "=== Memory Usage ==="
ps aux | grep python3 | grep -v grep | awk '{print $2, $6, $11}' | column -t

echo ""
echo "=== Recent Errors ==="
sudo journalctl -u btc-scalp-scanner -n 5 | grep -i error || echo "No recent errors"
EOF

chmod +x check_scanners.sh
./check_scanners.sh
```

---

## Automated Startup on Boot

Services are automatically enabled to start on boot:

```bash
# Verify services are enabled
sudo systemctl is-enabled btc-scalp-scanner
sudo systemctl is-enabled btc-swing-scanner
# etc...

# Disable auto-start if needed
sudo systemctl disable btc-scalp-scanner

# Re-enable auto-start
sudo systemctl enable btc-scalp-scanner
```

---

## Performance Optimization

### Increase File Descriptors

```bash
# Edit limits
sudo nano /etc/security/limits.conf

# Add these lines
* soft nofile 65536
* hard nofile 65536

# Apply
sudo sysctl -p
```

### Optimize Python

```bash
# Use PyPy for better performance (optional)
pip install pypy3

# Or use Cython for critical paths
pip install cython
```

### Monitor Resource Usage

```bash
# Install monitoring tools
sudo apt-get install -y htop iotop

# Monitor in real-time
htop

# Check I/O
sudo iotop
```

---

## Support and Debugging

### Enable Debug Logging

Edit `config/unified_config.json`:

```json
"logging": {
  "level": "DEBUG",
  "file": "logs/scanner.log",
  "rotation": "daily",
  "retention_days": 7
}
```

Restart scanners:

```bash
sudo bash deployment/restart_all_scanners.sh
```

### Collect Diagnostic Information

```bash
# Create diagnostic bundle
mkdir -p diagnostics
cp config/unified_config.json diagnostics/
sudo journalctl -u btc-scalp-scanner -n 1000 > diagnostics/btc-scalp.log
ps aux | grep python3 > diagnostics/processes.txt
free -h > diagnostics/memory.txt
df -h > diagnostics/disk.txt

# Create archive
tar -czf diagnostics.tar.gz diagnostics/
```

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Create virtual environment
3. ✅ Install services
4. ✅ Start scanners
5. ✅ Verify status
6. ✅ Monitor logs
7. ✅ Configure alerts
8. ✅ Set up monitoring

For issues, check logs and refer to troubleshooting section above.
