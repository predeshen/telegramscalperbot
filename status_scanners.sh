#!/bin/bash
# Check status of all trading scanner services

echo "=========================================="
echo "Trading Scanner Status"
echo "=========================================="
echo

sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner --no-pager

echo
echo "=========================================="
echo "Quick Summary"
echo "=========================================="
echo

for service in btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner; do
    status=$(systemctl is-active $service)
    if [ "$status" = "active" ]; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: $status"
    fi
done
