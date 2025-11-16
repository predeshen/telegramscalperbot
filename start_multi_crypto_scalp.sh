#!/bin/bash
# Multi-Crypto Scalping Scanner (BTC, ETH, SOL - 1m/5m/15m)

echo "========================================"
echo "Multi-Crypto Scalping Scanner Starting..."
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ using your package manager"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Checking dependencies..."
pip install -r requirements.txt --quiet

# Create logs directory if it doesn't exist
mkdir -p logs

# Start scanner
echo ""
echo "Starting Multi-Crypto Scalping Scanner..."
echo "Symbols: BTC, ETH, SOL"
echo "Timeframes: 1m, 5m, 15m"
echo "Press Ctrl+C to stop"
echo ""
python3 main_multi_symbol.py --config config/multi_crypto_scalp.json

# Deactivate virtual environment on exit
deactivate
