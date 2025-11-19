#!/bin/bash
# Restart all trading scanner services with code updates

echo "=========================================="
echo "Restarting All Trading Scanners"
echo "=========================================="
echo

# Define all scanner services
LEGACY_SCANNERS="btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner"
MULTI_SYMBOL_SCANNERS="multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner"

# Pull latest code changes
echo "Pulling latest code from repository..."
git pull

# Check if there are any uncommitted changes and stash them
if ! git diff-index --quiet HEAD --; then
    echo "Stashing local changes..."
    git stash
fi

echo

# Stop all services first
echo "Stopping legacy scanners..."
sudo systemctl stop $LEGACY_SCANNERS 2>/dev/null

echo "Stopping multi-symbol scanners..."
sudo systemctl stop $MULTI_SYMBOL_SCANNERS 2>/dev/null

echo "Waiting 2 seconds..."
sleep 2

# Start all services
echo "Starting legacy scanners..."
sudo systemctl start $LEGACY_SCANNERS 2>/dev/null

echo "Starting multi-symbol scanners..."
sudo systemctl start $MULTI_SYMBOL_SCANNERS 2>/dev/null

echo "Waiting 3 seconds for services to initialize..."
sleep 3

# Check status
echo
echo "=========================================="
echo "Service Status"
echo "=========================================="
echo
echo "Legacy Scanners:"
sudo systemctl status $LEGACY_SCANNERS --no-pager 2>/dev/null | grep -E "Active:|Loaded:"

echo
echo "Multi-Symbol Scanners:"
sudo systemctl status $MULTI_SYMBOL_SCANNERS --no-pager 2>/dev/null | grep -E "Active:|Loaded:"

echo
echo "=========================================="
echo "Checking for Failed Services"
echo "=========================================="
echo

# Check for any failed services and show their logs
for service in $LEGACY_SCANNERS $MULTI_SYMBOL_SCANNERS; do
    if systemctl is-failed --quiet $service 2>/dev/null; then
        echo "⚠️  $service is FAILED - Last 10 log lines:"
        sudo journalctl -u $service -n 10 --no-pager
        echo
    fi
done

echo
echo "=========================================="
echo "Restart Complete!"
echo "=========================================="
echo "Check your Telegram for startup messages."
echo
echo "To monitor a specific scanner in real-time:"
echo "  sudo journalctl -u <scanner-name> -f"
echo
echo "Example:"
echo "  sudo journalctl -u btc-us100-scanner -f"
