#!/bin/bash
# Deploy fixes to cloud VM and restart scanners

echo "=========================================="
echo "Deploying Fixes to Cloud VM"
echo "=========================================="
echo

# Commit the US100 symbol fix
echo "Committing US100 symbol support fix..."
git add src/symbol_context.py src/signal_detector.py
git commit -m "Fix: Add US100/NASDAQ symbol support to prevent 'Unknown symbol' warnings"

# Push to repository
echo "Pushing changes to repository..."
git push

echo
echo "=========================================="
echo "Fixes deployed to repository!"
echo "=========================================="
echo
echo "Now run this on your cloud VM:"
echo "  ./restart_scanners.sh"
echo
echo "This will:"
echo "  1. Pull the latest code (including US100 fix)"
echo "  2. Stop all scanners"
echo "  3. Start all scanners with the fixes"
echo
