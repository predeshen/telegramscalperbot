#!/bin/bash
# Deploy BTC Swing Trading Scanner

echo "=========================================="
echo "BTC Swing Scanner Deployment"
echo "=========================================="

# Check if already running
if screen -list | grep -q "btc_swing"; then
    echo "⚠️  Swing scanner already running in screen session 'btc_swing'"
    echo "To view: screen -r btc_swing"
    echo "To stop: screen -X -S btc_swing quit"
    exit 0
fi

# Start in screen session
echo "🚀 Starting swing scanner in background..."
screen -dmS btc_swing python main_swing.py

sleep 2

# Check if started
if screen -list | grep -q "btc_swing"; then
    echo "✅ Swing scanner started successfully!"
    echo ""
    echo "Commands:"
    echo "  View logs:    tail -f logs/scanner_swing.log"
    echo "  Attach:       screen -r btc_swing"
    echo "  Detach:       Ctrl+A, then D"
    echo "  Stop:         screen -X -S btc_swing quit"
    echo ""
    echo "Monitoring timeframes: 15m, 1h, 4h, 1d"
    echo "Checking every 60 seconds"
else
    echo "❌ Failed to start swing scanner"
    exit 1
fi
