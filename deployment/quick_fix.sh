#!/bin/bash

echo "=========================================="
echo "Quick Fix for BTC Scalp Scanner"
echo "=========================================="
echo ""

# Stop the scanner
echo "1. Stopping BTC Scalp Scanner..."
sudo systemctl stop btc-scalp-scanner
echo "✓ Stopped"
echo ""

# Activate venv and install dependencies
echo "2. Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Verify installation
echo "3. Verifying installation..."
python3 -c "import ccxt; print('✓ ccxt installed')" || echo "✗ ccxt failed"
python3 -c "import pandas; print('✓ pandas installed')" || echo "✗ pandas failed"
echo ""

# Test main.py
echo "4. Testing main.py..."
timeout 5 python3 main.py 2>&1 | head -20 || true
echo ""

# Restart scanner
echo "5. Restarting BTC Scalp Scanner..."
sudo systemctl restart btc-scalp-scanner
sleep 2
echo ""

# Check status
echo "6. Checking status..."
sudo systemctl status btc-scalp-scanner
echo ""

echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
