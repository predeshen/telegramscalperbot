#!/bin/bash
# Restart All Scanners Script
# Restarts all 8 trading scanners

echo "Restarting all trading scanners..."
echo ""

systemctl restart btc-scalp-scanner
echo "✓ BTC Scalp Scanner restarted"

systemctl restart btc-swing-scanner
echo "✓ BTC Swing Scanner restarted"

systemctl restart gold-scalp-scanner
echo "✓ Gold Scalp Scanner restarted"

systemctl restart gold-swing-scanner
echo "✓ Gold Swing Scanner restarted"

systemctl restart us30-scalp-scanner
echo "✓ US30 Scalp Scanner restarted"

systemctl restart us30-swing-scanner
echo "✓ US30 Swing Scanner restarted"

systemctl restart us100-scanner
echo "✓ US100 Scanner restarted"

systemctl restart multi-crypto-scanner
echo "✓ Multi-Crypto Scanner restarted"

echo ""
echo "All scanners restarted successfully!"
echo ""
echo "Check status with: systemctl status btc-scalp-scanner"
echo "View logs with: journalctl -u btc-scalp-scanner -f"
echo ""

