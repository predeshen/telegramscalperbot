# Trading Scanner System - Deployment Guide

## Overview

This guide covers the installation, configuration, and operation of the unified trading scanner system with 8 independent scanners for BTC, Gold, US30, US100, and multi-crypto assets.

## System Architecture

The system consists of:
- **8 Independent Scanners**: BTC Scalp, BTC Swing, Gold Scalp, Gold Swing, US30 Scalp, US30 Swing, US100, Multi-Crypto
- **Unified Data Source**: Multi-provider fallback (Binance → Twelve Data → Alpha Vantage → MT5)
- **Strategy Detection Engine**: Pluggable strategies with market-condition-based priority
- **Signal Quality Filter**: 7-factor confluence system with confidence scoring
- **Intelligent TP/SL Calculator**: Historical price action-based placement
- **Unified Alerting**: Email (SMTP) and Telegram notifications
- **Trade Tracking**: Automatic TP/SL monitoring and notifications

## Prerequisites

- Ubuntu 20.04+ or Debian 11+
- Python 3.9+
- 2GB RAM minimum
- 10GB disk space
- Internet connection (outbound only)

## Installation

### 1. Fresh Installation on New VM

```bash
# Clone repository
git clone <repository-url>
cd trading-scanners

# Run fresh install script (requires root)
sudo bash deployment/fresh_install.sh
```

This will:
- Install Python and dependencies
- Create scanner user and directories
- Install systemd services
- Configure auto-start on boot

### 2. Manual Installation

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create scanner user
sudo useradd -m -s /bin/bash scanner

# Create directories
sudo mkdir -p /opt/trading-scanners
sudo mkdir -p /etc/trading-scanners
sudo mkdir -p /var/log/trading-scanners

# Copy files
sudo cp -r . /opt/trading-scanners
sudo chown -R scanner:scanner /opt/trading-scanners

# Install Python dependencies
cd /opt/trading-scanners
sudo -u scanner pip3 install --user -r requirements.txt
```

## Configuration

### 1. Edit Configuration File

```bash
sudo nano /etc/trading-scanners/config.json
```

### 2. Required Settings

#### SMTP Configuration (Email Alerts)

```json
{
  "smtp": {
    "server": "mail.example.com",
    "port": 465,
    "user": "alerts@example.com",
    "password": "your_password",
    "from_email": "alerts@example.com",
    "to_email": "trader@example.com",
    "use_ssl": true
  }
}
```

#### Telegram Configuration (Optional)

```json
{
  "telegram": {
    "enabled": true,
    "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "chat_id": "your_chat_id"
  }
}
```

#### Data Providers (Optional)

```json
{
  "data_providers": {
    "alpha_vantage_key": "your_key",
    "twelve_data_key": "your_key",
    "preferred_provider": null
  }
}
```

### 3. Asset-Specific Configuration

```json
{
  "asset_specific": {
    "BTC": {
      "min_confluence_factors": 4,
      "min_confidence_score": 3,
      "volume_thresholds": {
        "scalp": 1.3,
        "swing": 1.2
      }
    },
    "XAUUSD": {
      "min_confluence_factors": 4,
      "min_confidence_score": 3,
      "volume_thresholds": {
        "scalp": 1.4,
        "swing": 1.3
      }
    }
  }
}
```

## Service Management

### Start All Scanners

```bash
sudo bash deployment/start_all_scanners.sh
```

Or individually:

```bash
sudo systemctl start btc-scalp-scanner
sudo systemctl start btc-swing-scanner
sudo systemctl start gold-scalp-scanner
# ... etc
```

### Stop All Scanners

```bash
sudo bash deployment/stop_all_scanners.sh
```

### Restart All Scanners

```bash
sudo bash deployment/restart_all_scanners.sh
```

### Check Status

```bash
sudo systemctl status btc-scalp-scanner
sudo systemctl status btc-swing-scanner
# ... etc
```

### View Logs

```bash
# Follow live logs
sudo journalctl -u btc-scalp-scanner -f

# View last 100 lines
sudo journalctl -u btc-scalp-scanner -n 100

# View logs from last hour
sudo journalctl -u btc-scalp-scanner --since "1 hour ago"
```

## Monitoring

### System Health

```bash
# Check all scanner status
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner

# Check disk usage
df -h /var/log/trading-scanners

# Check memory usage
free -h
```

### Signal Monitoring

Signals are logged to:
- `/var/log/trading-scanners/scanner.log` (application logs)
- Email alerts (configured SMTP)
- Telegram alerts (if enabled)
- Excel reports (if enabled)

## Troubleshooting

### Scanner Won't Start

```bash
# Check logs
sudo journalctl -u btc-scalp-scanner -n 50

# Check configuration syntax
python3 -c "import json; json.load(open('/etc/trading-scanners/config.json'))"

# Check permissions
ls -la /opt/trading-scanners
ls -la /etc/trading-scanners
```

### No Signals Detected

1. **Check data freshness**: Logs should show "Fresh data" messages
2. **Verify market conditions**: Signals require specific confluence conditions
3. **Check timeframe data**: Logs should show "Loaded X candles"
4. **Verify configuration**: Check min_confluence_factors and min_confidence_score

### Email Alerts Not Working

```bash
# Test SMTP connection
python3 << 'EOF'
import smtplib
server = smtplib.SMTP_SSL('mail.example.com', 465, timeout=10)
server.login('alerts@example.com', 'password')
print('SMTP connection successful')
server.quit()
EOF
```

### Telegram Alerts Not Working

1. Verify bot token is correct (from @BotFather)
2. Verify chat ID is correct (from @userinfobot)
3. Start a conversation with your bot first (send `/start`)
4. Check that `python-telegram-bot` is installed

### High Memory Usage

- Reduce buffer size in code (default 500 candles)
- Reduce log retention days
- Check for memory leaks in logs

### WebSocket Disconnects

- Normal behavior - auto-reconnects with exponential backoff
- Check network stability
- Verify firewall allows outbound connections

## Performance Tuning

### Polling Interval

Default: 10 seconds

To change, edit the polling loop call in `src/base_scanner.py`:

```python
scanner.run_polling_loop(interval_seconds=15)  # 15 seconds
```

### Buffer Size

Default: 500 candles per timeframe

To change, edit `src/base_scanner.py`:

```python
df, is_fresh = self.data_client.get_latest_candles(
    self.symbol,
    timeframe,
    limit=1000  # Increase to 1000
)
```

### Data Freshness Threshold

Default: 300 seconds (5 minutes)

To change, edit `src/unified_data_source.py`:

```python
data_config = DataSourceConfig(
    freshness_threshold_seconds=600  # 10 minutes
)
```

## Backup and Recovery

### Backup Configuration

```bash
sudo cp /etc/trading-scanners/config.json /etc/trading-scanners/config.json.backup
```

### Backup Logs

```bash
sudo tar -czf trading-scanners-logs-$(date +%Y%m%d).tar.gz /var/log/trading-scanners/
```

### Restore Configuration

```bash
sudo cp /etc/trading-scanners/config.json.backup /etc/trading-scanners/config.json
sudo systemctl restart btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

## Security

### File Permissions

```bash
# Configuration file (sensitive credentials)
sudo chmod 600 /etc/trading-scanners/config.json

# Log directory
sudo chmod 755 /var/log/trading-scanners

# Application directory
sudo chmod 755 /opt/trading-scanners
```

### Environment Variables

Instead of storing passwords in config file:

```bash
# Create environment file
sudo nano /etc/trading-scanners/env

# Add credentials
SMTP_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# Update systemd service
sudo nano /etc/systemd/system/btc-scalp-scanner.service

# Add under [Service]
EnvironmentFile=/etc/trading-scanners/env

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart btc-scalp-scanner
```

### Firewall

```bash
# Allow outbound connections only
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
```

## Maintenance

### Regular Tasks

- **Daily**: Check logs for errors
- **Weekly**: Verify all scanners are running
- **Monthly**: Review signal quality and adjust thresholds
- **Quarterly**: Update dependencies

### Update System

```bash
# Update Python dependencies
sudo -u scanner pip3 install --user --upgrade -r requirements.txt

# Update application code
cd /opt/trading-scanners
git pull origin main
sudo systemctl restart btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

### Clean Up Logs

```bash
# Remove logs older than 7 days
sudo find /var/log/trading-scanners -name "*.log" -mtime +7 -delete

# Compress old logs
sudo find /var/log/trading-scanners -name "*.log" -mtime +1 -exec gzip {} \;
```

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u btc-scalp-scanner -f`
2. Review configuration: `cat /etc/trading-scanners/config.json`
3. Test connectivity: `python3 -c "import ccxt; print(ccxt.binance().load_markets())"`
4. Check system resources: `top`, `df -h`, `free -h`

