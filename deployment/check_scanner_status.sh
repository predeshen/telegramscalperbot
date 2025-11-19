#!/bin/bash

# Check status of all trading scanners
# This script displays the status of all 8 scanner services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scanner services
SCANNERS=(
    "btc-scalp-scanner"
    "btc-swing-scanner"
    "gold-scalp-scanner"
    "gold-swing-scanner"
    "us30-scalp-scanner"
    "us30-swing-scanner"
    "us100-scanner"
    "multi-crypto-scanner"
)

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Trading Scanner Status Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}⚠️  Note: Some information may be limited without root privileges${NC}"
    echo ""
fi

# Track overall status
all_running=true
running_count=0
stopped_count=0

# Check each scanner
for scanner in "${SCANNERS[@]}"; do
    # Get service status (suppress errors)
    status=$(systemctl is-active "$scanner" 2>&1 || true)
    
    # Check if service exists
    if [[ "$status" == *"Unit"* ]] || [[ "$status" == *"not-found"* ]]; then
        status="not-installed"
    fi
    
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✓${NC} ${scanner}: ${GREEN}RUNNING${NC}"
        ((running_count++))
        
        # Get PID and memory usage if running
        pid=$(systemctl show -p MainPID --value "$scanner" 2>/dev/null || echo "")
        if [ -n "$pid" ] && [ "$pid" != "0" ]; then
            # Get memory usage
            mem=$(ps -p "$pid" -o %mem= 2>/dev/null || echo "N/A")
            cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null || echo "N/A")
            echo "  └─ PID: $pid | CPU: ${cpu}% | Memory: ${mem}%"
        fi
    elif [ "$status" = "not-installed" ]; then
        echo -e "${YELLOW}⚠${NC} ${scanner}: ${YELLOW}NOT INSTALLED${NC}"
        ((stopped_count++))
    else
        echo -e "${RED}✗${NC} ${scanner}: ${RED}STOPPED${NC}"
        ((stopped_count++))
        all_running=false
        
        # Show last few lines of log if available
        log_file="/home/predeshen/telegramscalperbot/logs/${scanner}.log"
        if [ -f "$log_file" ]; then
            last_error=$(tail -n 1 "$log_file" 2>/dev/null || echo "")
            if [ -n "$last_error" ]; then
                echo "  └─ Last log: ${last_error:0:80}..."
            fi
        fi
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "Summary: ${GREEN}${running_count} running${NC}, ${RED}${stopped_count} stopped${NC}"
echo -e "${BLUE}========================================${NC}"

# Exit with appropriate code
if [ "$all_running" = true ]; then
    echo -e "${GREEN}✓ All scanners are running${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some scanners are not running${NC}"
    exit 1
fi
