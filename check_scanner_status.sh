#!/bin/bash

# Scanner Status Check Script
# Displays the status of all 8 trading scanners

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Scanner list
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

# Log directory
LOG_DIR="/home/predeshen/telegramscalperbot/logs"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         TRADING SCANNER STATUS CHECK${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check systemd service status
echo -e "${YELLOW}📊 SYSTEMD SERVICE STATUS:${NC}"
echo ""

active_count=0
inactive_count=0

for scanner in "${SCANNERS[@]}"; do
    status=$(systemctl is-active "$scanner" 2>/dev/null || echo "inactive")
    
    if [ "$status" = "active" ]; then
        echo -e "${GREEN}✓${NC} $scanner: ${GREEN}RUNNING${NC}"
        ((active_count++))
    else
        echo -e "${RED}✗${NC} $scanner: ${RED}STOPPED${NC}"
        ((inactive_count++))
    fi
done

echo ""
echo -e "${BLUE}Summary: ${GREEN}$active_count running${NC}, ${RED}$inactive_count stopped${NC}${NC}"
echo ""

# Check log files
echo -e "${YELLOW}📝 LOG FILE STATUS:${NC}"
echo ""

for scanner in "${SCANNERS[@]}"; do
    log_file="$LOG_DIR/${scanner}.log"
    
    if [ -f "$log_file" ]; then
        file_size=$(du -h "$log_file" | cut -f1)
        last_modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$log_file" 2>/dev/null || stat --format="%y" "$log_file" 2>/dev/null | cut -d' ' -f1-2)
        
        echo -e "${GREEN}✓${NC} $scanner.log: $file_size (updated: $last_modified)"
    else
        echo -e "${RED}✗${NC} $scanner.log: ${RED}NOT FOUND${NC}"
    fi
done

echo ""

# Check for recent errors in logs
echo -e "${YELLOW}⚠️  RECENT ERRORS (last 5 minutes):${NC}"
echo ""

error_found=0

for scanner in "${SCANNERS[@]}"; do
    log_file="$LOG_DIR/${scanner}.log"
    
    if [ -f "$log_file" ]; then
        # Find errors from the last 5 minutes
        error_count=$(grep -c "ERROR\|CRITICAL\|Exception" "$log_file" 2>/dev/null | tail -20 || echo "0")
        
        if [ "$error_count" -gt 0 ]; then
            echo -e "${RED}⚠️  $scanner: $error_count errors found${NC}"
            error_found=1
        fi
    fi
done

if [ $error_found -eq 0 ]; then
    echo -e "${GREEN}✓ No recent errors detected${NC}"
fi

echo ""

# Check process details
echo -e "${YELLOW}🔍 PROCESS DETAILS:${NC}"
echo ""

for scanner in "${SCANNERS[@]}"; do
    pid=$(systemctl show -p MainPID --value "$scanner" 2>/dev/null || echo "0")
    
    if [ "$pid" != "0" ] && [ "$pid" != "" ]; then
        # Get memory and CPU usage
        if ps -p "$pid" > /dev/null 2>&1; then
            mem=$(ps -p "$pid" -o %mem= 2>/dev/null | xargs || echo "N/A")
            cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | xargs || echo "N/A")
            echo -e "${GREEN}✓${NC} $scanner (PID: $pid) - CPU: $cpu%, Memory: $mem%"
        fi
    else
        echo -e "${RED}✗${NC} $scanner - Not running"
    fi
done

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Check complete at $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
