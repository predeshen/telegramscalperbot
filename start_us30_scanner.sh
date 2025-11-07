#!/bin/bash

# US30 Scanner Startup Script
# This runs the scanner specifically for US30/USD

echo "Starting US30 Scanner..."

# Activate virtual environment
source venv/bin/activate

# Run scanner with US30 config
python3 main.py --config config/us30_config.json

echo "US30 Scanner stopped"
