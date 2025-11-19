#!/bin/bash

echo "=========================================="
echo "BTC Scalp Scanner Diagnostic"
echo "=========================================="
echo ""

# Check Python
echo "1. Checking Python..."
python3 --version
which python3
echo ""

# Check if main.py exists
echo "2. Checking main.py..."
if [ -f "main.py" ]; then
    echo "✓ main.py found"
    head -20 main.py
else
    echo "✗ main.py NOT found"
fi
echo ""

# Check dependencies
echo "3. Checking Python dependencies..."
python3 -c "import pandas; print('✓ pandas')" 2>&1 || echo "✗ pandas missing"
python3 -c "import numpy; print('✓ numpy')" 2>&1 || echo "✗ numpy missing"
python3 -c "import ccxt; print('✓ ccxt')" 2>&1 || echo "✗ ccxt missing"
python3 -c "import requests; print('✓ requests')" 2>&1 || echo "✗ requests missing"
echo ""

# Check config
echo "4. Checking configuration..."
if [ -f "config/unified_config.json" ]; then
    echo "✓ unified_config.json found"
    python3 -c "import json; json.load(open('config/unified_config.json'))" && echo "✓ Config is valid JSON" || echo "✗ Config JSON invalid"
else
    echo "✗ unified_config.json NOT found"
fi
echo ""

# Try to run main.py with error output
echo "5. Running main.py (first 30 seconds)..."
timeout 30 python3 main.py 2>&1 || true
echo ""

# Check imports
echo "6. Checking imports in main.py..."
python3 << 'EOF'
import sys
import traceback

try:
    print("Attempting to import main module...")
    import main
    print("✓ main module imported successfully")
except Exception as e:
    print(f"✗ Error importing main: {e}")
    traceback.print_exc()
EOF
echo ""

# Check environment
echo "7. Checking environment..."
env | grep -E "PYTHON|PATH|HOME" || echo "No relevant env vars"
echo ""

# Check working directory
echo "8. Checking working directory..."
pwd
ls -la | head -20
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
