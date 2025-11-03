#!/bin/bash
# Stop all trading scanner services

echo "=========================================="
echo "Stopping All Trading Scanners"
echo "=========================================="
echo

sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

echo
echo "All scanners stopped."
echo
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner --no-pager
