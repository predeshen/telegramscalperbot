#!/bin/bash
# Check scanner services status and logs

echo "=========================================="
echo "Scanner Services Status Check"
echo "=========================================="
echo

# Check all services
echo "Service Status:"
echo "---------------"
for service in btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner; do
    status=$(systemctl is-active $service 2>/dev/null)
    if [ "$status" = "active" ]; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: $status"
    fi
done

echo
echo "=========================================="
echo "Checking .env Configuration"
echo "=========================================="
echo

if [ -f .env ]; then
    echo "✓ .env file exists"
    
    # Check for Telegram credentials (without showing them)
    if grep -q "TELEGRAM_BOT_TOKEN=" .env && ! grep -q "TELEGRAM_BOT_TOKEN=$" .env; then
        echo "✓ TELEGRAM_BOT_TOKEN is set"
    else
        echo "✗ TELEGRAM_BOT_TOKEN is missing or empty"
    fi
    
    if grep -q "TELEGRAM_CHAT_ID=" .env && ! grep -q "TELEGRAM_CHAT_ID=your_chat_id_here" .env; then
        echo "✓ TELEGRAM_CHAT_ID is set"
    else
        echo "✗ TELEGRAM_CHAT_ID is missing or set to placeholder"
        echo "  Run: nano .env"
        echo "  And add your chat ID from @userinfobot"
    fi
else
    echo "✗ .env file not found!"
fi

echo
echo "=========================================="
echo "Recent Log Entries (Last 10 lines each)"
echo "=========================================="
echo

for log in logs/scanner.log logs/scanner_swing.log logs/gold_scanner.log logs/gold_swing_scanner.log logs/us30_scalp_scanner.log logs/us30_swing_scanner.log; do
    if [ -f "$log" ]; then
        echo
        echo "--- $log ---"
        tail -n 10 "$log" 2>/dev/null || echo "  (empty or unreadable)"
    fi
done

echo
echo "=========================================="
echo "US30 Scanner Errors (if any)"
echo "=========================================="
echo

# Check US30 scanner errors
if systemctl is-active us30-scalp-scanner >/dev/null 2>&1; then
    echo "✓ US30 Scalp Scanner: Running"
else
    echo "✗ US30 Scalp Scanner: Failed"
    echo "Error details:"
    sudo journalctl -u us30-scalp-scanner -n 20 --no-pager | grep -i error || echo "  (checking logs...)"
fi

if systemctl is-active us30-swing-scanner >/dev/null 2>&1; then
    echo "✓ US30 Swing Scanner: Running"
else
    echo "✗ US30 Swing Scanner: Failed"
    echo "Error details:"
    sudo journalctl -u us30-swing-scanner -n 20 --no-pager | grep -i error || echo "  (checking logs...)"
fi

echo
echo "=========================================="
echo "Quick Fix Commands"
echo "=========================================="
echo

echo "View live logs:"
echo "  tail -f logs/scanner.log"
echo
echo "Check specific service:"
echo "  sudo systemctl status btc-scalp-scanner"
echo
echo "Restart all services:"
echo "  sudo systemctl restart btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner"
echo
echo "View systemd logs:"
echo "  sudo journalctl -u btc-scalp-scanner -f"
echo
