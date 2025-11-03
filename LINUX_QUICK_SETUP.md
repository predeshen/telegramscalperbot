# 🐧 Linux VM - Quick Setup Guide

## One-Command Installation

```bash
sudo bash deployment/install_services.sh
```

That's it! The script will:
- ✅ Check Python installation
- ✅ Install dependencies
- ✅ Create .env file
- ✅ Set up log directories
- ✅ Install all 6 systemd services
- ✅ Configure everything automatically

---

## After Installation

### 1. Add Telegram Chat ID (Required)

```bash
nano .env

# Change this line:
TELEGRAM_CHAT_ID=your_chat_id_here

# To your actual chat ID (get from @userinfobot on Telegram):
TELEGRAM_CHAT_ID=123456789

# Save: Ctrl+O, Enter, Ctrl+X
```

### 2. Enable Services (Start on Boot)

```bash
sudo systemctl enable btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner
```

### 3. Start Services

```bash
sudo systemctl start btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner
```

### 4. Verify Running

```bash
# Check all services
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner

# View logs
tail -f logs/*.log
```

---

## Common Commands

### Start All Services
```bash
sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner
```

### Stop All Services
```bash
sudo systemctl stop btc-*-scanner gold-*-scanner us30-*-scanner
```

### Restart All Services
```bash
sudo systemctl restart btc-*-scanner gold-*-scanner us30-*-scanner
```

### Check Status
```bash
sudo systemctl status btc-*-scanner gold-*-scanner us30-*-scanner
```

### View Logs (Live)
```bash
# Systemd logs
sudo journalctl -u btc-scalp-scanner -f

# Application logs
tail -f logs/scanner.log

# All logs
tail -f logs/*.log
```

---

## Service Features

✅ **Automatic Restart** - Services restart if they crash
✅ **Start on Boot** - Services start automatically when VM boots
✅ **Resource Limits** - Memory and file descriptor limits enforced
✅ **Security** - Runs as non-root user with restricted permissions
✅ **Logging** - Logs to both systemd journal and log files

---

## Troubleshooting

### Service Won't Start
```bash
# Check status
sudo systemctl status btc-scalp-scanner

# View logs
sudo journalctl -u btc-scalp-scanner -n 50

# Check for errors
tail -f logs/scanner.log
```

### Check All Services
```bash
# Create quick check script
cat > check.sh << 'EOF'
#!/bin/bash
for s in btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner; do
    status=$(systemctl is-active $s)
    [ "$status" = "active" ] && echo "✓ $s" || echo "✗ $s: $status"
done
EOF
chmod +x check.sh
./check.sh
```

---

## Migration from Screen Sessions

### 1. Stop Screen Sessions
```bash
screen -list
screen -S btc_scanner -X quit
screen -S btc_swing -X quit
# ... etc
```

### 2. Install Services
```bash
sudo bash deployment/install_services.sh
```

### 3. Start Services
```bash
sudo systemctl start btc-*-scanner gold-*-scanner us30-*-scanner
```

---

## Why Systemd > Screen?

| Feature | Screen | Systemd |
|---------|--------|---------|
| Auto-restart on crash | ❌ | ✅ |
| Start on boot | ❌ | ✅ |
| Resource limits | ❌ | ✅ |
| Centralized logging | ❌ | ✅ |
| Security hardening | ❌ | ✅ |
| Survives disconnect | ⚠️ | ✅ |

---

## Full Documentation

See `LINUX_SERVICE_SETUP.md` for complete documentation including:
- Advanced configuration
- Monitoring setup
- Security settings
- Troubleshooting guide

---

**Ready to deploy? Run the installation command above!** 🚀
