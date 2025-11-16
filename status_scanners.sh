#!/bin/bash
# Check status of all trading scanner services

echo "=========================================="
echo "Trading Scanner Status"
echo "=========================================="
echo

# Legacy single-symbol scanners
echo "Legacy Scanners:"
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner --no-pager

echo
echo "Multi-Symbol Scanners:"
sudo systemctl status multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner --no-pager 2>/dev/null || echo "Multi-symbol scanners not installed"

echo
echo "=========================================="
echo "Quick Summary"
echo "=========================================="
echo

echo "Legacy Scanners:"
for service in btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner; do
    status=$(systemctl is-active $service)
    if [ "$status" = "active" ]; then
        echo "  ✓ $service: RUNNING"
    else
        echo "  ✗ $service: $status"
    fi
done

echo
echo "Multi-Symbol Scanners:"
for service in multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner; do
    if systemctl list-unit-files | grep -q "^$service.service"; then
        status=$(systemctl is-active $service)
        if [ "$status" = "active" ]; then
            echo "  ✓ $service: RUNNING"
        else
            echo "  ✗ $service: $status"
        fi
    else
        echo "  - $service: not installed"
    fi
done
