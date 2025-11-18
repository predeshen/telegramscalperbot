# Install US100 Scanner Service

## Issue
The `btc-us100-scanner.service` was not installed during the main installation because it wasn't in the deployment directory when `install_services.sh` ran.

## Solution

Run these commands on your **Linux server** (not Windows):

```bash
# Navigate to your project directory
cd ~/telegramscalperbot

# Make the install script executable
chmod +x install_us100_service.sh

# Run the installer
sudo bash install_us100_service.sh
```

## What the Script Does

1. Detects your username and project directory
2. Creates the service file with correct paths
3. Installs it to `/etc/systemd/system/`
4. Reloads systemd

## After Installation

```bash
# Enable service to start on boot
sudo systemctl enable btc-us100-scanner

# Start the service
sudo systemctl start btc-us100-scanner

# Check status
sudo systemctl status btc-us100-scanner

# View logs
sudo journalctl -u btc-us100-scanner -f
```

## Alternative: Manual Installation

If you prefer to install manually:

```bash
# Create service file
sudo nano /etc/systemd/system/btc-us100-scanner.service
```

Paste this content (replace `predeshen` and path if different):

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

Then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable btc-us100-scanner
sudo systemctl start btc-us100-scanner

# Check status
sudo systemctl status btc-us100-scanner
```

## Verify Installation

```bash
# Check if service file exists
ls -la /etc/systemd/system/btc-us100-scanner.service

# Check service status
sudo systemctl status btc-us100-scanner

# View recent logs
sudo journalctl -u btc-us100-scanner -n 50
```

## Troubleshooting

### Service won't start
```bash
# Check Python path
which python3

# Check if main_us100.py exists
ls -la ~/telegramscalperbot/main_us100.py

# Check permissions
ls -la ~/telegramscalperbot/

# View detailed logs
sudo journalctl -u btc-us100-scanner -xe
```

### Python command not found
```bash
# The error "python: command not found" means you need to use python3
# The service file already uses python3, so this should work

# Verify python3 is installed
python3 --version
```

### Missing dependencies
```bash
cd ~/telegramscalperbot
pip3 install -r requirements.txt
```

## Quick Test

Before installing as a service, test the scanner directly:

```bash
cd ~/telegramscalperbot
python3 main_us100.py
```

Press Ctrl+C to stop. If it runs without errors, you're ready to install the service.

## All Scanner Services

After installing US100, you'll have these services available:

```bash
# Legacy single-symbol scanners
btc-scalp-scanner
btc-swing-scanner
gold-scalp-scanner
gold-swing-scanner
us30-scalp-scanner
us30-swing-scanner
us30-momentum-scanner
btc-us100-scanner  ← NEW

# Multi-symbol scanners (recommended)
multi-crypto-scalp-scanner
multi-crypto-swing-scanner
multi-fx-scalp-scanner
multi-mixed-scanner
```

## Start All Scanners

```bash
# Start all legacy scanners (including US100)
sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner

# Or start just US100
sudo systemctl start btc-us100-scanner

# Check status of all
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner
```

## Monitor All Scanners

```bash
# View logs for all scanners
tail -f ~/telegramscalperbot/logs/*.log

# Or view specific scanner
tail -f ~/telegramscalperbot/logs/us100_scanner.log

# Or use journalctl
sudo journalctl -u btc-us100-scanner -f
```

---

**Note:** Run all these commands on your Linux server, not on Windows.
