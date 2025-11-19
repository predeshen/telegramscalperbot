# BTC Scalp Scanner Troubleshooting

## Issue: BTC Scalp Scanner Failing to Start

The BTC Scalp Scanner is exiting with status code 1. This guide will help you diagnose and fix the issue.

## Step 1: Run Diagnostic Script

```bash
cd ~/telegramscalperbot
bash deployment/diagnose_btc_scalp.sh
```

This will check:
- Python installation
- main.py file exists
- All dependencies installed
- Configuration file valid
- Actual error messages

## Step 2: Check Common Issues

### Issue A: Missing Dependencies

If you see "ModuleNotFoundError", install dependencies:

```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list | grep -E "pandas|numpy|ccxt|requests"
```

### Issue B: Configuration File Missing

If config file is missing:

```bash
# Check if config exists
ls -la config/unified_config.json

# If missing, copy from repo
git pull origin main
```

### Issue C: Import Errors in main.py

Check what main.py is trying to import:

```bash
# Try importing main module
python3 -c "import main" 2>&1
```

If you see errors, check:
1. All imports exist in src/
2. No circular imports
3. All required modules installed

### Issue D: Runtime Error

Run main.py directly to see the actual error:

```bash
# Activate venv
source venv/bin/activate

# Run with full output
python3 main.py 2>&1 | head -100
```

## Step 3: Check Service Configuration

```bash
# View service file
cat /etc/systemd/system/btc-scalp-scanner.service

# Check if paths are correct
grep "ExecStart" /etc/systemd/system/btc-scalp-scanner.service
```

The service file should have:
```
ExecStart=/usr/bin/python3 /home/predeshen/telegramscalperbot/main.py
```

## Step 4: Manual Test

```bash
# Navigate to project
cd ~/telegramscalperbot

# Activate venv
source venv/bin/activate

# Run main.py
python3 main.py

# If it works, the issue is with the service configuration
# If it fails, the issue is with the code/dependencies
```

## Step 5: Check Logs

```bash
# View systemd logs
sudo journalctl -u btc-scalp-scanner -n 100

# View application logs
tail -f logs/btc_scalp_scans.log 2>/dev/null || echo "Log file not created yet"
```

## Common Solutions

### Solution 1: Reinstall Dependencies

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Solution 2: Recreate Virtual Environment

```bash
# Remove old venv
rm -rf venv

# Create new venv
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Solution 3: Update Service File

```bash
# Stop service
sudo systemctl stop btc-scalp-scanner

# Reinstall services
sudo bash deployment/install_services.sh

# Start service
sudo systemctl start btc-scalp-scanner
```

### Solution 4: Check Python Path

```bash
# Verify Python is correct
which python3
/usr/bin/python3 --version

# If different, update service file
sudo nano /etc/systemd/system/btc-scalp-scanner.service

# Change ExecStart to use correct Python path
# Then reload and restart
sudo systemctl daemon-reload
sudo systemctl restart btc-scalp-scanner
```

## Step 6: Enable Debug Logging

Edit `config/unified_config.json`:

```json
"logging": {
  "level": "DEBUG",
  "file": "logs/scanner.log",
  "rotation": "daily",
  "retention_days": 7
}
```

Then restart:

```bash
sudo systemctl restart btc-scalp-scanner
sudo journalctl -u btc-scalp-scanner -f
```

## Step 7: Test Other Scanners

If BTC Scalp fails but others work, the issue is specific to main.py:

```bash
# Check if other scanners work
sudo systemctl status btc-swing-scanner
sudo systemctl status gold-scalp-scanner

# If they work, issue is with main.py specifically
```

## Advanced Debugging

### Check for Syntax Errors

```bash
python3 -m py_compile main.py
```

### Check for Import Cycles

```bash
python3 << 'EOF'
import sys
import importlib.util

spec = importlib.util.spec_from_file_location("main", "main.py")
module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
    print("✓ Module loaded successfully")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

### Check Environment Variables

```bash
# View all env vars
env | sort

# Check if required vars are set
echo "ALPHA_VANTAGE_KEY: $ALPHA_VANTAGE_KEY"
echo "TWELVE_DATA_KEY: $TWELVE_DATA_KEY"
echo "TELEGRAM_BOT_TOKEN: $TELEGRAM_BOT_TOKEN"
```

## If Still Failing

1. **Collect diagnostic info**:
   ```bash
   bash deployment/diagnose_btc_scalp.sh > diagnostic_report.txt 2>&1
   ```

2. **Check system resources**:
   ```bash
   free -h
   df -h
   ps aux | grep python3
   ```

3. **Review recent changes**:
   ```bash
   git log --oneline -10
   git diff HEAD~1
   ```

4. **Try alternative scanner**:
   ```bash
   # If BTC Scalp fails, try BTC Swing
   sudo systemctl start btc-swing-scanner
   sudo systemctl status btc-swing-scanner
   ```

## Quick Fix Checklist

- [ ] Run diagnostic script
- [ ] Check Python version (3.8+)
- [ ] Verify all dependencies installed
- [ ] Check config file exists and is valid
- [ ] Verify service file paths are correct
- [ ] Test running main.py manually
- [ ] Check logs for actual error message
- [ ] Reinstall dependencies if needed
- [ ] Recreate virtual environment if needed
- [ ] Update service files if needed

## Support

If you're still stuck:

1. Run: `bash deployment/diagnose_btc_scalp.sh`
2. Check: `sudo journalctl -u btc-scalp-scanner -n 50`
3. Try: `python3 main.py 2>&1 | head -50`
4. Share the output for debugging

## Next Steps

Once BTC Scalp is working:

1. Verify other scanners are running
2. Check logs for signals
3. Verify alerts are being sent
4. Monitor resource usage
5. Set up monitoring/alerting
