# Fix Null Bytes - Final Solution

## The Problem

The files still have null bytes even after `git reset --hard`. This means the local files are corrupted and git can't fix them.

## The Solution

**Complete fresh installation by removing and re-cloning the repository.**

---

## Step-by-Step Fix

### 1. Stop All Services

```bash
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner
```

### 2. Backup Your .env File

```bash
cp ~/telegramscalperbot/.env /tmp/scanner_env_backup
```

### 3. Remove Corrupted Directory

```bash
cd ~
rm -rf telegramscalperbot
```

### 4. Fresh Clone from GitHub

```bash
git clone https://github.com/predeshen/telegramscalperbot.git
cd telegramscalperbot
```

### 5. Restore .env File

```bash
cp /tmp/scanner_env_backup .env
```

### 6. Install Dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 7. Verify Files Are Clean

```bash
python3 -c "from src.signal_detector import SignalDetector; print('✓ Fixed!')"
```

**You should see:** `✓ Fixed!`

**If you still see an error**, the GitHub repository itself has the issue. Let me know.

### 8. Reinstall Services

```bash
sudo bash deployment/install_services.sh
```

Press `y` when prompted.

### 9. Start Services

```bash
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner
```

### 10. Check Status

```bash
sudo systemctl status btc-scalp-scanner
```

Should show: `Active: active (running)`

### 11. View Logs

```bash
tail -f logs/scanner.log
```

You should see:
- "Scanner is now running"
- "Telegram message sent successfully"

---

## Quick One-Liner (All Steps)

```bash
sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner && \
cp ~/telegramscalperbot/.env /tmp/scanner_env_backup && \
cd ~ && rm -rf telegramscalperbot && \
git clone https://github.com/predeshen/telegramscalperbot.git && \
cd telegramscalperbot && \
cp /tmp/scanner_env_backup .env && \
python3 -m pip install -r requirements.txt && \
python3 -c "from src.signal_detector import SignalDetector; print('✓ Fixed!')" && \
sudo bash deployment/install_services.sh
```

Then start services:
```bash
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner
```

---

## After Fix

Check everything is working:

```bash
# Check all services
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner

# Watch logs
tail -f logs/scanner.log

# Should see Telegram messages on your phone!
```

---

## If Still Having Issues

The null bytes might be in the GitHub repository itself. Let me know and I'll fix the source files.

---

**This will completely fix the null bytes issue by starting fresh!**
