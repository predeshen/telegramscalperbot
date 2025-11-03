# Linux Systemd Service Setup Guide

## Overview

Run your trading scanners as systemd services for:
- ✅ Automatic startup on boot
- ✅ Automatic restart on crash
- ✅ Better resource management
- ✅ Centralized logging
- ✅ No need for screen sessions

---

## Quick Installation

### 1. Install Services (One Command)

```bash
sudo bash deployment/install_services.sh
```

This will:
- Check Python installation
- Install dependencies
- Create .env file (if needed)
- Set up log directories
- Install all 6 service files
- Configure systemd

### 2. Configure Telegram

```bash
# Edit .env file
nano .env

# Add your chat ID (get from @userinfobot on Telegram)
TELEGRAM_CHAT_ID=123456789
```

### 3. Enable Services (Start on Boot)

```bash
# Enable all services
sudo systemctl enable btc-scalp-scanner
sudo systemctl enable btc-swing-scanner
sudo systemctl enable gold-scalp-scanner
sudo systemctl enable gold-swing-scanner
sudo systemctl enable us30-scalp-scanner
sudo systemctl enable us30-swing-scanner
```

### 4. Start Services

```bash
# Start all services
sudo systemctl start btc-scalp-scanner
sudo systemctl start btc-swing-scanner
sudo systemctl start gold-scalp-scanner
sudo systemctl start gold-swing-scanner
sudo systemctl start us30-scalp-scanner
sudo systemctl start us30-swing-scanner
```

---

## Service Management

### Start Services

```bash
# Start individual service
sudo systemctl start btc-scalp-scanner

# Start all services at once
sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner
```

### Stop Services

```bash
# Stop individual service
sudo systemctl stop btc-scalp-scanner

# Stop all services
sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner
```

### Restart Services

```bash
# Restart individual service
sudo systemctl restart btc-scalp-scanner

# Restart all services
sudo systemctl restart btc-*-scanner gold-*-scanner us30-*-scanner
```

### Check Status

```bash
# Check individual service
sudo systemctl status btc-scalp-scanner

# Check all services
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner
```

### View Logs

```bash
# View systemd logs (live)
sudo journalctl -u btc-scalp-scanner -f

# View application logs (live)
tail -f logs/scanner.log

# View all scanner logs
tail -f logs/*.log
```

---

## Available Services

### 1. btc-scalp-scanner.service
- **Script:** main.py
- **Timeframes:** 1m, 5m
- **Log:** logs/scanner.log

### 2. btc-swing-scanner.service
- **Script:** main_swing.py
- **Timeframes:** 15m, 1h, 4h, 1d
- **Log:** logs/scanner_swing.log

### 3. gold-scalp-scanner.service
- **Script:** xauusd_scanner/main_gold.py
- **Timeframes:** 1m, 5m
- **Log:** logs/gold_scanner.log

### 4. gold-swing-scanner.service
- **Script:** xauusd_scanner/main_gold_swing.py
- **Timeframes:** 1h, 4h, 1d
- **Log:** logs/gold_swing_scanner.log

### 5. us30-scalp-scanner.service
- **Script:** us30_scanner/main_us30_scalp.py
- **Timeframes:** 5m, 15m
- **Log:** logs/us30_scalp_scanner.log

### 6. us30-swing-scanner.service
- **Script:** us30_scanner/main_us30_swing.py
- **Timeframes:** 4h, 1d
- **Log:** logs/us30_swing_scanner.log

---

## Service Features

### Automatic Restart
- Services restart automatically if they crash
- 10-second delay between restart attempts
- Prevents rapid restart loops

### Resource Limits
- Memory limit: 512MB per service
- File descriptor limit: 4096
- Prevents resource exhaustion

### Security Hardening
- Runs as non-root user
- Private /tmp directory
- No privilege escalation
- Read-only system files

### Logging
- Logs to both systemd journal and log files
- Unbuffered output for real-time logging
- Automatic log rotation by systemd

---

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status btc-scalp-scanner

# View detailed logs
sudo journalctl -u btc-scalp-scanner -n 50

# Check for errors
sudo journalctl -u btc-scalp-scanner -p err
```

### Service Keeps Restarting

```bash
# Check logs for errors
tail -f logs/scanner.log

# Check Python dependencies
python3 -m pip install -r requirements.txt

# Verify .env file
cat .env
```

### Can't See Logs

```bash
# Check log file permissions
ls -la logs/

# Fix permissions if needed
sudo chown -R $USER:$USER logs/

# Check systemd journal
sudo journalctl -u btc-scalp-scanner --since "1 hour ago"
```

### Service Not Starting on Boot

```bash
# Check if enabled
sudo systemctl is-enabled btc-scalp-scanner

# Enable if not
sudo systemctl enable btc-scalp-scanner

# Check for failed services
sudo systemctl list-units --failed
```

---

## Advanced Configuration

### Change User

Edit service file:
```bash
sudo nano /etc/systemd/system/btc-scalp-scanner.service

# Change these lines:
User=your_username
Group=your_username

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart btc-scalp-scanner
```

### Change Working Directory

Edit service file:
```bash
sudo nano /etc/systemd/system/btc-scalp-scanner.service

# Change this line:
WorkingDirectory=/path/to/your/project

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart btc-scalp-scanner
```

### Increase Memory Limit

Edit service file:
```bash
sudo nano /etc/systemd/system/btc-scalp-scanner.service

# Change this line:
MemoryMax=1G

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart btc-scalp-scanner
```

---

## Monitoring

### Check All Services

```bash
# Create monitoring script
cat > check_scanners.sh << 'EOF'
#!/bin/bash
echo "Scanner Status:"
for service in btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner; do
    status=$(systemctl is-active $service)
    if [ "$status" = "active" ]; then
        echo "✓ $service: $status"
    else
        echo "✗ $service: $status"
    fi
done
EOF

chmod +x check_scanners.sh
./check_scanners.sh
```

### Set Up Monitoring Cron Job

```bash
# Add to crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * /path/to/check_scanners.sh
```

---

## Comparison: Screen vs Systemd

### Screen Sessions (Old Method)
- ❌ Manual restart required
- ❌ No automatic startup on boot
- ❌ Can lose sessions on disconnect
- ❌ Manual log management
- ❌ No resource limits

### Systemd Services (New Method)
- ✅ Automatic restart on crash
- ✅ Automatic startup on boot
- ✅ Persistent across disconnects
- ✅ Centralized logging
- ✅ Resource limits enforced
- ✅ Better security

---

## Migration from Screen

### 1. Stop Screen Sessions

```bash
# List screen sessions
screen -list

# Kill all scanner screens
screen -S btc_scanner -X quit
screen -S btc_swing -X quit
screen -S xau_scalp -X quit
screen -S xau_swing -X quit
screen -S us30_scalp -X quit
screen -S us30_swing -X quit
```

### 2. Install Services

```bash
sudo bash deployment/install_services.sh
```

### 3. Start Services

```bash
sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner
```

### 4. Verify

```bash
# Check all services are running
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner

# Check logs
tail -f logs/*.log
```

---

## Uninstallation

### Remove Services

```bash
# Stop all services
sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner

# Disable all services
sudo systemctl disable btc-*-scanner gold-*-scanner us30-*-scanner

# Remove service files
sudo rm /etc/systemd/system/btc-*-scanner.service
sudo rm /etc/systemd/system/gold-*-scanner.service
sudo rm /etc/systemd/system/us30-*-scanner.service

# Reload systemd
sudo systemctl daemon-reload
```

---

## Support

If you encounter issues:
1. Check service status: `sudo systemctl status <service-name>`
2. View logs: `sudo journalctl -u <service-name> -f`
3. Check application logs: `tail -f logs/*.log`
4. Verify .env file has correct credentials
5. Ensure Python dependencies are installed

---

**Recommended:** Use systemd services for production deployments on Linux servers.
