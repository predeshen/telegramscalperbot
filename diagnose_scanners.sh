#!/bin/bash
# Diagnose Scanner Issues
# Helps identify why scanners are failing

echo "=========================================="
echo "Scanner Diagnostics Tool"
echo "=========================================="
echo

# Function to check scanner logs
check_scanner() {
    local scanner_name=$1
    echo "Checking $scanner_name..."
    echo "----------------------------------------"
    
    # Get last error
    sudo journalctl -u $scanner_name -n 50 --no-pager | grep -A 10 "Traceback\|Error\|Exception" | tail -20
    
    if [ $? -eq 0 ]; then
        echo "✗ Found errors in $scanner_name"
    else
        echo "✓ No obvious errors in $scanner_name logs"
    fi
    echo
}

# Check failing scanners
echo "Checking failing scanners..."
echo

check_scanner "btc-swing-scanner"
check_scanner "us30-momentum-scanner"
check_scanner "multi-crypto-scalp-scanner"
check_scanner "multi-crypto-swing-scanner"
check_scanner "multi-fx-scalp-scanner"
check_scanner "multi-mixed-scanner"

echo "=========================================="
echo "Quick Fixes"
echo "=========================================="
echo
echo "For us30-momentum-scanner:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl restart us30-momentum-scanner"
echo
echo "For other scanners, check the errors above and:"
echo "  1. Verify Python dependencies: pip3 install -r requirements.txt"
echo "  2. Check file permissions: ls -la main_*.py"
echo "  3. Test manually: python3 main_swing.py"
echo

