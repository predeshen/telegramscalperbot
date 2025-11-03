#!/bin/bash
# Restart all trading scanner services

echo "=========================================="
echo "Restarting All Trading Scanners"
echo "=========================================="
echo

# Stop all services first
echo "Stopping all scanners..."
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

echo "Waiting 2 seconds..."
sleep 2

# Start all services
echo "Starting all scanners..."
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

echo "Waiting 3 seconds for services to initialize..."
sleep 3

# Check status
echo
echo "=========================================="
echo "Service Status"
echo "=========================================="
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner --no-pager

echo
echo "=========================================="
echo "Restart Complete!"
echo "=========================================="
echo "Check your Telegram for startup messages."
