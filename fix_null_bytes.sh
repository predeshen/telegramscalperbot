#!/bin/bash
# Fix null bytes in Python files
# Run this on your Linux VM: bash fix_null_bytes.sh

echo "Fixing null bytes in Python files..."

# Stop all services first
echo "Stopping services..."
sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner

# Remove null bytes from Python files
echo "Removing null bytes..."
find src/ -name "*.py" -type f -exec sed -i 's/\x0//g' {} \;
find . -maxdepth 1 -name "*.py" -type f -exec sed -i 's/\x0//g' {} \;

echo "✓ Null bytes removed"

# Verify the fix
echo "Verifying files..."
python3 -c "from src.signal_detector import SignalDetector; print('✓ signal_detector.py is valid')"
python3 -c "from src.indicator_calculator import IndicatorCalculator; print('✓ indicator_calculator.py is valid')"
python3 -c "from src.market_data_client import MarketDataClient; print('✓ market_data_client.py is valid')"

echo
echo "✓ All files fixed!"
echo
echo "Now start the services:"
echo "sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner"
