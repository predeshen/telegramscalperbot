# Fix Scanner Crash Issue

## Problem

Your scanners are crashing immediately after starting because the `openpyxl` library (required for Excel reporting) is not installed on your server.

## Quick Fix

Run these commands on your server:

```bash
# Install openpyxl
pip3 install openpyxl>=3.1.0

# Or run the install script
chmod +x install_excel_reporting.sh
./install_excel_reporting.sh

# Restart scanners
./stop_all_scanners.sh
./start_all_scanners.sh --monitor
```

## Detailed Steps

### 1. Check Dependencies

```bash
python3 check_dependencies.py
```

This will show you which dependencies are missing.

### 2. Install Missing Dependencies

```bash
# Install all requirements
pip3 install -r requirements.txt

# Or install just openpyxl
pip3 install openpyxl>=3.1.0
```

### 3. Verify Installation

```bash
python3 -c "import openpyxl; print(openpyxl.__version__)"
```

Should output: `3.1.5` or similar

### 4. Restart Scanners

```bash
# Stop all scanners
./stop_all_scanners.sh

# Start all scanners
./start_all_scanners.sh --monitor
```

### 5. Verify Scanners Are Running

```bash
# Check screen sessions
screen -list

# Should show 6 sessions:
# - btc_scanner
# - btc_swing
# - xau_scalp
# - xau_swing
# - us30_scalp
# - us30_swing
```

### 6. Check Logs

```bash
# BTC Scalp
tail -f logs/scanner.log

# Should see:
# [INFO] Excel reporting enabled
# [INFO] All components initialized successfully
# [INFO] Scanner is now running
```

## Alternative: Disable Excel Reporting Temporarily

If you want to run the scanners without Excel reporting for now:

### Option 1: Disable in Config

Edit each config file and set:
```json
"excel_reporting": {
  "enabled": false
}
```

### Option 2: Set Password to DISABLED

Edit each config file and set:
```json
"smtp": {
  "password": "DISABLED"
}
```

Then restart scanners:
```bash
./stop_all_scanners.sh
./start_all_scanners.sh --monitor
```

## Troubleshooting

### Scanner Still Crashes

1. **Check Python version:**
   ```bash
   python3 --version
   ```
   Should be Python 3.8 or higher

2. **Check if openpyxl is installed:**
   ```bash
   pip3 list | grep openpyxl
   ```

3. **Try installing with --user flag:**
   ```bash
   pip3 install --user openpyxl>=3.1.0
   ```

4. **Check for import errors:**
   ```bash
   python3 -c "from src.excel_reporter import ExcelReporter"
   ```

### Permission Issues

If you get permission errors:
```bash
pip3 install --user openpyxl>=3.1.0
```

### Virtual Environment

If using a virtual environment:
```bash
source venv/bin/activate
pip install openpyxl>=3.1.0
```

## Verify Excel Reporting Works

After installing openpyxl and restarting scanners:

1. **Check logs for Excel reporter:**
   ```bash
   tail -f logs/scanner.log | grep -i excel
   ```
   
   Should see:
   ```
   [INFO] Excel reporting enabled
   [INFO] ExcelReporter initialized: logs/btc_scalp_scans.xlsx
   ```

2. **Check Excel files are created:**
   ```bash
   ls -lh logs/*.xlsx
   ```
   
   Should see files like:
   - `btc_scalp_scans.xlsx`
   - `btc_swing_scans.xlsx`
   - etc.

3. **Wait 5 minutes for initial email**
   Check your email at predeshen@gmail.com

## Summary

The issue is simply that `openpyxl` is not installed on your server. Install it with:

```bash
pip3 install openpyxl>=3.1.0
```

Then restart your scanners and everything should work!
