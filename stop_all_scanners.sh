#!/bin/bash
# Stop All Trading Scanners

echo "=========================================="
echo "Stopping All Trading Scanners"
echo "=========================================="

# Load environment for Telegram notifications
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Function to send Telegram message
send_telegram() {
    local message="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="${message}" \
            -d parse_mode="HTML" > /dev/null
    fi
}

# Stop each scanner
stopped_count=0

if screen -list | grep -q "btc_scanner"; then
    echo "Stopping BTC Scalping Scanner..."
    screen -X -S btc_scanner quit
    ((stopped_count++))
fi

if screen -list | grep -q "btc_swing"; then
    echo "Stopping BTC Swing Scanner..."
    screen -X -S btc_swing quit
    ((stopped_count++))
fi

if screen -list | grep -q "xau_scalp"; then
    echo "Stopping XAU/USD Scalping Scanner..."
    screen -X -S xau_scalp quit
    ((stopped_count++))
fi

if screen -list | grep -q "xau_swing"; then
    echo "Stopping XAU/USD Swing Scanner..."
    screen -X -S xau_swing quit
    ((stopped_count++))
fi

if screen -list | grep -q "scanner_monitor"; then
    echo "Stopping Health Monitor..."
    screen -X -S scanner_monitor quit
fi

echo ""
if [ $stopped_count -eq 0 ]; then
    echo "No scanners were running"
else
    echo "✅ Stopped $stopped_count scanner(s)"
    send_telegram "🛑 <b>All Scanners Stopped</b>%0A%0AStopped $stopped_count scanner(s). Trading monitoring is now inactive."
fi

echo ""
echo "Remaining screens:"
screen -list || echo "  None"
