#!/bin/bash
# Fresh installation - completely remove and re-clone repository
# This will fix the null bytes issue permanently

echo "=========================================="
echo "Fresh Installation Script"
echo "=========================================="
echo

# Stop all services
echo "Stopping all services..."
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

# Save .env file
echo "Backing up .env file..."
if [ -f .env ]; then
    cp .env /tmp/scanner_env_backup
    echo "✓ .env backed up to /tmp/scanner_env_backup"
fi

# Go to parent directory
cd ..

# Remove corrupted directory
echo "Removing corrupted directory..."
rm -rf telegramscalperbot

# Fresh clone from GitHub
echo "Cloning fresh copy from GitHub..."
git clone https://github.com/predeshen/telegramscalperbot.git

# Enter directory
cd telegramscalperbot

# Restore .env file
echo "Restoring .env file..."
if [ -f /tmp/scanner_env_backup ]; then
    cp /tmp/scanner_env_backup .env
    echo "✓ .env restored"
fi

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt --quiet

# Verify files are clean
echo
echo "Verifying files..."
python3 -c "from src.signal_detector import SignalDetector; print('✓ signal_detector.py is clean')" || echo "✗ Still has issues"
python3 -c "from src.indicator_calculator import IndicatorCalculator; print('✓ indicator_calculator.py is clean')" || echo "✗ Still has issues"
python3 -c "from src.market_data_client import MarketDataClient; print('✓ market_data_client.py is clean')" || echo "✗ Still has issues"

# Reinstall services
echo
echo "Reinstalling services..."
sudo bash deployment/install_services.sh

echo
echo "=========================================="
echo "Fresh Installation Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Start services:"
echo "   sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner"
echo
echo "2. Check status:"
echo "   sudo systemctl status btc-scalp-scanner"
echo
echo "3. View logs:"
echo "   tail -f logs/scanner.log"
echo
