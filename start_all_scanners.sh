#!/bin/bash
# Unified Startup Script for All Trading Scanners
# Starts BTC Scalping, BTC Swing, and XAU/USD scanners with health monitoring

set -e

echo "=========================================="
echo "Trading Scanners Deployment"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set"
    echo "Please create .env file with:"
    echo "TELEGRAM_BOT_TOKEN=your_token"
    echo "TELEGRAM_CHAT_ID=your_chat_id"
    exit 1
fi

# Function to send Telegram message
send_telegram() {
    local message="$1"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="${TELEGRAM_CHAT_ID}" \
        -d text="${message}" \
        -d parse_mode="HTML" > /dev/null
}

# Function to start a scanner
start_scanner() {
    local name="$1"
    local script="$2"
    local screen_name="$3"
    
    echo ""
    echo "Starting $name..."
    
    # Check if already running
    if screen -list | grep -q "$screen_name"; then
        echo "⚠️  $name already running in screen '$screen_name'"
        return 0
    fi
    
    # Start in screen session
    screen -dmS "$screen_name" bash -c "python $script; echo 'Scanner stopped. Press enter to close.'; read"
    
    sleep 2
    
    # Verify started
    if screen -list | grep -q "$screen_name"; then
        echo "✅ $name started successfully"
        send_telegram "🚀 <b>$name Started</b>%0A%0AScanner is now running and monitoring the market.%0AScreen: $screen_name"
        return 0
    else
        echo "❌ Failed to start $name"
        send_telegram "❌ <b>$name Failed to Start</b>%0A%0APlease check logs and restart manually."
        return 1
    fi
}

# Function to check scanner health
check_health() {
    local screen_name="$1"
    local scanner_name="$2"
    
    if ! screen -list | grep -q "$screen_name"; then
        echo "⚠️  $scanner_name is not running!"
        send_telegram "⚠️ <b>$scanner_name Stopped</b>%0A%0AScanner has stopped unexpectedly. Please investigate.%0AScreen: $screen_name"
        return 1
    fi
    return 0
}

echo ""
echo "🚀 Starting all scanners..."
echo ""

# Start BTC Scalping Scanner (1m/5m)
start_scanner "BTC Scalping Scanner" "main.py" "btc_scanner"

# Start BTC Swing Scanner (15m/1h/4h/1d)
start_scanner "BTC Swing Scanner" "main_swing.py" "btc_swing"

# Start XAU/USD Gold Scanner (when ready)
if [ -f "xauusd_scanner/main_gold.py" ]; then
    start_scanner "XAU/USD Gold Scanner" "xauusd_scanner/main_gold.py" "xau_scanner"
else
    echo "⏳ XAU/USD scanner not yet available (still in development)"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete"
echo "=========================================="
echo ""
echo "Active Scanners:"
screen -list | grep -E "(btc_scanner|btc_swing|xau_scanner)" || echo "  None running"
echo ""
echo "Commands:"
echo "  View all:     screen -list"
echo "  Attach BTC:   screen -r btc_scanner"
echo "  Attach Swing: screen -r btc_swing"
echo "  Attach Gold:  screen -r xau_scanner"
echo "  Detach:       Ctrl+A, then D"
echo "  Stop all:     ./stop_all_scanners.sh"
echo ""
echo "Logs:"
echo "  BTC Scalp:    tail -f logs/scanner.log"
echo "  BTC Swing:    tail -f logs/scanner_swing.log"
echo "  XAU/USD:      tail -f logs/scanner_gold.log"
echo ""

# Send summary notification
send_telegram "📊 <b>All Scanners Deployed</b>%0A%0A✅ BTC Scalping (1m/5m)%0A✅ BTC Swing (15m/1h/4h/1d)%0A%0AMonitoring active. You'll receive alerts for all signals."

# Optional: Start health monitoring in background
if [ "$1" == "--monitor" ]; then
    echo "Starting health monitor..."
    screen -dmS scanner_monitor bash -c "
        while true; do
            sleep 300  # Check every 5 minutes
            
            # Check each scanner
            if ! screen -list | grep -q 'btc_scanner'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>BTC Scalping Scanner Stopped</b>%0A%0APlease restart: screen -r btc_scanner' \
                    -d parse_mode='HTML' > /dev/null
            fi
            
            if ! screen -list | grep -q 'btc_swing'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>BTC Swing Scanner Stopped</b>%0A%0APlease restart: screen -r btc_swing' \
                    -d parse_mode='HTML' > /dev/null
            fi
            
            if screen -list | grep -q 'xau_scanner'; then
                if ! screen -list | grep -q 'xau_scanner'; then
                    curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                        -d chat_id='${TELEGRAM_CHAT_ID}' \
                        -d text='⚠️ <b>XAU/USD Scanner Stopped</b>%0A%0APlease restart: screen -r xau_scanner' \
                        -d parse_mode='HTML' > /dev/null
                fi
            fi
        done
    "
    echo "✅ Health monitor started (checks every 5 minutes)"
fi

echo ""
echo "Tip: Run with --monitor flag to enable automatic health checks"
echo "     ./start_all_scanners.sh --monitor"
