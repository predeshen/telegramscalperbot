# Scanner Deployment & Troubleshooting Guide

## Quick Fix Deployment (From Local Machine)

### Step 1: Deploy the US100 Fix
```bash
# Run this on your LOCAL machine
./deploy_fixes.sh
```

This will:
- Commit the US100/NASDAQ symbol support fix
- Push changes to your repository

### Step 2: Apply Fixes on Cloud VM
```bash
# SSH into your cloud VM, then run:
cd ~/telegramscalperbot
./restart_scanners.sh
```

This will:
- Pull latest code (including US100 fix)
- Stop all scanners gracefully
- Start all scanners with fixes applied
- Show status of all services
- Display logs for any failed services

---

## Current Issues Fixed

### ✅ US100/NASDAQ Symbol Support
**Problem**: US100 scanner showing "Unknown symbol 'US100', defaulting to BTC"

**Fix Applied**:
- Added US100 to `src/symbol_context.py` with proper NASDAQ configuration
- Added US100 to symbol maps in `src/signal_detector.py`
- US100 now properly recognized as NASDAQ index (^IXIC)

---

## Troubleshooting Failed Scanners

### Check Individual Scanner Status
```bash
sudo systemctl status btc-scalp-scanner
sudo systemctl status btc-swing-scanner
```

### View Real-Time Logs
```bash
# Monitor specific scanner
sudo journalctl -u btc-us100-scanner -f

# View last 50 lines
sudo journalctl -u btc-scalp-scanner -n 50
```

### Common Issues

#### 1. Scanner Exits with Code 1
**Symptoms**: Service shows "activating (auto-restart)" or "exit-code"

**Diagnosis**:
```bash
sudo journalctl -u btc-scalp-scanner -n 100
```

**Common Causes**:
- Missing configuration file
- Invalid Telegram credentials
- Python dependency issues
- Symbol configuration errors

#### 2. No Signals/Heartbeats After Startup
**Symptoms**: Scanner runs but no Telegram messages

**Check**:
- Verify Telegram bot token in config
- Check if bot is blocked or chat_id is wrong
- Look for "Failed to send message" in logs
- Verify market is open (for indices/forex)

#### 3. Memory Limit Warnings
**Symptoms**: "Unit uses MemoryLimit=; please use MemoryMax="

**Fix**: Update systemd service files to use MemoryMax instead of MemoryLimit

---

## Monitoring Commands

### Quick Status Check
```bash
./status_scanners.sh
```

### Check All Scanner Logs
```bash
# View all scanner logs from last hour
sudo journalctl --since "1 hour ago" | grep -E "scanner|signal|alert"
```

### Monitor System Resources
```bash
# Check memory usage
free -h

# Check CPU usage
top -b -n 1 | head -20
```

---

## Emergency Procedures

### Stop All Scanners
```bash
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us30-momentum-scanner btc-us100-scanner multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner
```

### Restart Individual Scanner
```bash
sudo systemctl restart btc-us100-scanner
sudo journalctl -u btc-us100-scanner -f
```

### Reload Systemd After Config Changes
```bash
sudo systemctl daemon-reload
```

---

## Next Steps After Deployment

1. **Verify US100 Scanner**: Check that "Unknown symbol" warning is gone
   ```bash
   sudo journalctl -u btc-us100-scanner -f
   ```

2. **Monitor for Signals**: Wait for market activity and verify alerts come through

3. **Check Failed Scanners**: Investigate btc-scalp-scanner and btc-swing-scanner failures
   ```bash
   sudo journalctl -u btc-scalp-scanner -n 100
   sudo journalctl -u btc-swing-scanner -n 100
   ```

4. **Test Heartbeat**: Verify heartbeat messages are being sent to Telegram

---

## Support

If issues persist after applying fixes:
1. Check logs for specific error messages
2. Verify all configuration files are present
3. Ensure Python dependencies are installed
4. Check network connectivity to data sources
