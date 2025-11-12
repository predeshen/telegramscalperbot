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

# Function to start a scanner and wait for initialization
start_scanner() {
    local name="$1"
    local script="$2"
    local screen_name="$3"
    local log_file="$4"
    
    echo ""
    echo "Starting $name..."
    
    # Check if already running
    if screen -list | grep -q "$screen_name"; then
        echo "⚠️  $name already running in screen '$screen_name'"
        return 0
    fi
    
    # Start in screen session
    screen -dmS "$screen_name" bash -c "python3 $script; echo 'Scanner stopped. Press enter to close.'; read"
    
    echo "   Waiting for initialization..."
    
    # Wait for scanner to initialize (check log file)
    local max_wait=60  # Maximum 60 seconds
    local waited=0
    local initialized=false
    
    while [ $waited -lt $max_wait ]; do
        sleep 2
        waited=$((waited + 2))
        
        # Check if log file exists and contains initialization message
        if [ -f "$log_file" ]; then
            if grep -q "Scanner is now running" "$log_file" 2>/dev/null || \
               grep -q "All components initialized successfully" "$log_file" 2>/dev/null; then
                initialized=true
                break
            fi
        fi
        
        # Check if screen session still exists
        if ! screen -list | grep -q "$screen_name"; then
            echo "❌ $name crashed during startup"
            echo "   Check logs: tail -f $log_file"
            send_telegram "❌ <b>$name Failed to Start</b>%0A%0AScanner crashed during initialization. Check logs."
            return 1
        fi
        
        # Show progress
        if [ $((waited % 10)) -eq 0 ]; then
            echo "   Still initializing... (${waited}s)"
        fi
    done
    
    # Verify initialization
    if [ "$initialized" = true ]; then
        echo "✅ $name initialized and running"
        send_telegram "🚀 <b>$name Started</b>%0A%0AScanner is now running and monitoring the market.%0AScreen: $screen_name"
        return 0
    else
        echo "⚠️  $name started but initialization not confirmed (timeout after ${max_wait}s)"
        echo "   Scanner may still be starting. Check logs: tail -f $log_file"
        return 0
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
echo "   Each scanner will initialize before starting the next one."
echo ""

# Start BTC Scalping Scanner (1m/5m)
start_scanner "BTC Scalping Scanner" "main.py" "btc_scanner" "logs/scanner.log"

# Start BTC Swing Scanner (15m/1h/4h/1d)
start_scanner "BTC Swing Scanner" "main_swing.py" "btc_swing" "logs/scanner_swing.log"

# Start XAU/USD Gold Scalping Scanner (1m/5m)
if [ -f "xauusd_scanner/main_gold.py" ]; then
    start_scanner "XAU/USD Gold Scalping Scanner" "xauusd_scanner/main_gold.py" "xau_scalp" "logs/gold_scanner.log"
else
    echo "⏳ XAU/USD scalping scanner not yet available"
fi

# Start XAU/USD Gold Swing Scanner (15m/1h/4h/1d)
if [ -f "xauusd_scanner/main_gold_swing.py" ]; then
    start_scanner "XAU/USD Gold Swing Scanner" "xauusd_scanner/main_gold_swing.py" "xau_swing" "logs/gold_swing_scanner.log"
else
    echo "⏳ XAU/USD swing scanner not yet available"
fi

# Start US30 Scalping Scanner (5m/15m)
if [ -f "us30_scanner/main_us30_scalp.py" ]; then
    start_scanner "US30 Scalping Scanner" "us30_scanner/main_us30_scalp.py" "us30_scalp" "logs/us30_scalp_scanner.log"
else
    echo "⏳ US30 scalping scanner not yet available"
fi

# Start US30 Swing Scanner (4h/1d)
if [ -f "us30_scanner/main_us30_swing.py" ]; then
    start_scanner "US30 Swing Scanner" "us30_scanner/main_us30_swing.py" "us30_swing" "logs/us30_swing_scanner.log"
else
    echo "⏳ US30 swing scanner not yet available"
fi

# Start US30 Momentum Scanner (1m/5m/15m) - NEW AGGRESSIVE STRATEGY
if [ -f "main_us30.py" ]; then
    start_scanner "US30 Momentum Scanner" "main_us30.py" "us30_momentum" "logs/us30_momentum_scanner.log"
else
    echo "⏳ US30 momentum scanner not yet available"
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete"
echo "=========================================="
echo ""
echo "Active Scanners:"
screen -list | grep -E "(btc_scanner|btc_swing|xau_scalp|xau_swing|us30_scalp|us30_swing|us30_momentum)" || echo "  None running"
echo ""
echo "Commands:"
echo "  View all:          screen -list"
echo "  Attach BTC Scalp:  screen -r btc_scanner"
echo "  Attach BTC Swing:  screen -r btc_swing"
echo "  Attach Gold Scalp: screen -r xau_scalp"
echo "  Attach Gold Swing: screen -r xau_swing"
echo "  Attach US30 Scalp: screen -r us30_scalp"
echo "  Attach US30 Swing: screen -r us30_swing"
echo "  Attach US30 Momentum: screen -r us30_momentum"
echo "  Detach:            Ctrl+A, then D"
echo "  Stop all:          ./stop_all_scanners.sh"
echo ""
echo "Logs:"
echo "  BTC Scalp:         tail -f logs/scanner.log"
echo "  BTC Swing:         tail -f logs/scanner_swing.log"
echo "  Gold Scalp:        tail -f logs/gold_scanner.log"
echo "  Gold Swing:        tail -f logs/gold_swing_scanner.log"
echo "  US30 Scalp:        tail -f logs/us30_scalp_scanner.log"
echo "  US30 Swing:        tail -f logs/us30_swing_scanner.log"
echo "  US30 Momentum:     tail -f logs/us30_momentum_scanner.log"
echo ""

# Send summary notification
send_telegram "📊 <b>All Scanners Deployed</b>%0A%0A✅ BTC Scalping (1m/5m)%0A✅ BTC Swing (15m/1h/4h/1d)%0A✅ Gold Scalping (1m/5m)%0A✅ Gold Swing (1h/4h/1d)%0A✅ US30 Scalping (5m/15m)%0A✅ US30 Swing (4h/1d)%0A✅ US30 Momentum (1m/5m/15m) 🚀 NEW%0A%0AMonitoring active. You'll receive alerts for all signals."

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
            
            if ! screen -list | grep -q 'xau_scalp'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>Gold Scalping Scanner Stopped</b>%0A%0APlease restart: screen -r xau_scalp' \
                    -d parse_mode='HTML' > /dev/null
            fi
            
            if ! screen -list | grep -q 'xau_swing'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>Gold Swing Scanner Stopped</b>%0A%0APlease restart: screen -r xau_swing' \
                    -d parse_mode='HTML' > /dev/null
            fi
            
            if ! screen -list | grep -q 'us30_scalp'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>US30 Scalping Scanner Stopped</b>%0A%0APlease restart: screen -r us30_scalp' \
                    -d parse_mode='HTML' > /dev/null
            fi
            
            if ! screen -list | grep -q 'us30_swing'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>US30 Swing Scanner Stopped</b>%0A%0APlease restart: screen -r us30_swing' \
                    -d parse_mode='HTML' > /dev/null
            fi
            
            if ! screen -list | grep -q 'us30_momentum'; then
                curl -s -X POST 'https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage' \
                    -d chat_id='${TELEGRAM_CHAT_ID}' \
                    -d text='⚠️ <b>US30 Momentum Scanner Stopped</b>%0A%0APlease restart: screen -r us30_momentum' \
                    -d parse_mode='HTML' > /dev/null
            fi
        done
    "
    echo "✅ Health monitor started (checks every 5 minutes)"
fi

echo ""
echo "Tip: Run with --monitor flag to enable automatic health checks"
echo "     ./start_all_scanners.sh --monitor"
