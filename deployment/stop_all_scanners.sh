#!/bin/bash
# Stop All Scanners Script
# Stops all 8 trading scanners

echo "Stopping all trading scanners..."
echo ""

systemctl stop btc-scalp-scanner
echo "✓ BTC Scalp Scanner stopped"

systemctl stop btc-swing-scanner
echo "✓ BTC Swing Scanner stopped"

systemctl stop gold-scalp-scanner
echo "✓ Gold Scalp Scanner stopped"

systemctl stop gold-swing-scanner
echo "✓ Gold Swing Scanner stopped"

systemctl stop us30-scalp-scanner
echo "✓ US30 Scalp Scanner stopped"

systemctl stop us30-swing-scanner
echo "✓ US30 Swing Scanner stopped"

systemctl stop us100-scanner
echo "✓ US100 Scanner stopped"

systemctl stop multi-crypto-scanner
echo "✓ Multi-Crypto Scanner stopped"

echo ""
echo "All scanners stopped successfully!"
echo ""

