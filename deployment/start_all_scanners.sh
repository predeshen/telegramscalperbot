#!/bin/bash
# Start All Scanners Script
# Starts all 8 trading scanners

echo "Starting all trading scanners..."
echo ""

systemctl start btc-scalp-scanner
echo "✓ BTC Scalp Scanner started"

systemctl start btc-swing-scanner
echo "✓ BTC Swing Scanner started"

systemctl start gold-scalp-scanner
echo "✓ Gold Scalp Scanner started"

systemctl start gold-swing-scanner
echo "✓ Gold Swing Scanner started"

systemctl start us30-scalp-scanner
echo "✓ US30 Scalp Scanner started"

systemctl start us30-swing-scanner
echo "✓ US30 Swing Scanner started"

systemctl start us100-scanner
echo "✓ US100 Scanner started"

systemctl start multi-crypto-scanner
echo "✓ Multi-Crypto Scanner started"

echo ""
echo "All scanners started successfully!"
echo ""
echo "Check status with: systemctl status btc-scalp-scanner"
echo "View logs with: journalctl -u btc-scalp-scanner -f"
echo ""

