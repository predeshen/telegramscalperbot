#!/bin/bash
# Start all trading scanner services

echo "=========================================="
echo "Starting All Trading Scanners"
echo "=========================================="
echo

sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

echo "Waiting 3 seconds for services to initialize..."
sleep 3

echo
echo "=========================================="
echo "Service Status"
echo "=========================================="
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner --no-pager

echo
echo "All scanners started. Check Telegram for startup messages."
