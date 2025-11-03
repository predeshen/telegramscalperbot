# 🔧 Fix Null Bytes Error on Linux VM

## Problem

You're seeing this error:
```
ValueError: source code string cannot contain null bytes
```

This happened because the files got corrupted during editing. The fix is simple!

---

## Solution 1: Pull Clean Files from GitHub (Recommended)

```bash
# Stop all services
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

# Pull clean files from GitHub
git fetch origin
git reset --hard origin/main

# Verify the fix
python3 -c "from src.signal_detector import SignalDetector; print('✓ Fixed!')"

# Start services
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

# Check status
sudo systemctl status btc-scalp-scanner
```

---

## Solution 2: Remove Null Bytes Manually

```bash
# Stop services
sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner

# Remove null bytes from all Python files
find src/ -name "*.py" -type f -exec sed -i 's/\x0//g' {} \;
find . -maxdepth 1 -name "*.py" -type f -exec sed -i 's/\x0//g' {} \;

# Verify
python3 -c "from src.signal_detector import SignalDetector; print('✓ Fixed!')"

# Start services
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner
```

---

## Verify Services Are Running

```bash
# Check all services
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner

# View logs
tail -f logs/scanner.log
```

---

## Quick Commands

```bash
# Stop all
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

# Start all
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner

# Status all
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner
```

---

## After Fix

Once services are running, you should see:
- ✅ Services showing "active (running)"
- ✅ Logs showing "Scanner is now running"
- ✅ Telegram messages received
- ✅ No error messages

---

**Recommended:** Use Solution 1 (pull from GitHub) for clean files.
