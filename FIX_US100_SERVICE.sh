#!/bin/bash
# Quick fix to install US100 scanner service
# Run this on your Linux server: sudo bash FIX_US100_SERVICE.sh

set -e

echo "=========================================="
echo "Installing US100 Scanner Service"
echo "=========================================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get actual user
ACTUAL_USER="${SUDO_USER:-$USER}"

echo "User: $ACTUAL_USER"
echo "Project: $SCRIPT_DIR"
echo

# Check if service file template exists
if [ ! -f "$SCRIPT_DIR/deployment/btc-us100-scanner.service" ]; then
    echo "❌ Service template not found"
    echo "Creating service file directly..."
    
    # Create service file directly
    cat > /etc/systemd/system/btc-us100-scanner.service << EOF
[Unit]
Description=US100/NASDAQ Trading Scanner
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main_us100.py
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
EOF
else
    # Use template and update paths
    sed -e "s|/home/ubuntu/telegramscalperbot|$SCRIPT_DIR|g" \
        -e "s|/root/BTCUSDScanner|$SCRIPT_DIR|g" \
        -e "s|User=ubuntu|User=$ACTUAL_USER|g" \
        -e "s|User=root|User=$ACTUAL_USER|g" \
        -e "s|Group=ubuntu|Group=$ACTUAL_USER|g" \
        "$SCRIPT_DIR/deployment/btc-us100-scanner.service" > /etc/systemd/system/btc-us100-scanner.service
fi

echo "✓ Service file installed"

# Reload systemd
systemctl daemon-reload
echo "✓ Systemd reloaded"

echo
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo
echo "1. Enable service:"
echo "   sudo systemctl enable btc-us100-scanner"
echo
echo "2. Start service:"
echo "   sudo systemctl start btc-us100-scanner"
echo
echo "3. Check status:"
echo "   sudo systemctl status btc-us100-scanner"
echo
echo "4. View logs:"
echo "   sudo journalctl -u btc-us100-scanner -f"
echo

