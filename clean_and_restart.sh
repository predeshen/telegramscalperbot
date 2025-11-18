#!/bin/bash
# Clean all logs and restart scanners with fresh state
# WARNING: This deletes all historical data!

echo "=========================================="
echo "CLEAN RESTART - All Data Will Be Deleted"
echo "=========================================="
echo
echo "This will delete:"
echo "  - All log files (*.log*)"
echo "  - All Excel reports (*.xlsx)"
echo "  - All historical signal data"
echo
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo
echo "Stopping all scanners..."
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner multi-crypto-scanner

echo "Waiting 2 seconds..."
sleep 2

echo "Cleaning logs directory..."
rm -f logs/*.log*
rm -f logs/*.xlsx
echo "✓ Deleted all log files and Excel reports"

echo "Recreating log files with correct permissions..."
touch logs/scanner.log
touch logs/scanner_swing.log
touch logs/gold_scanner.log
touch logs/gold_swing_scanner.log
touch logs/us30_scalp_scanner.log
touch logs/us30_swing_scanner.log
touch logs/us30_momentum_scanner.log
touch logs/us100_scanner.log
touch logs/multi_crypto_scanner.log
chmod 644 logs/*.log
echo "✓ Log files recreated"

echo
echo "Starting all scanners with fresh state..."
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner multi-crypto-scanner

echo "Waiting 3 seconds for services to initialize..."
sleep 3

# Check status
echo
echo "=========================================="
echo "Service Status"
echo "=========================================="
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner multi-crypto-scanner --no-pager

echo
echo "=========================================="
echo "Clean Restart Complete!"
echo "=========================================="
echo "All scanners started with fresh state."
echo "Check your Telegram for startup messages."
