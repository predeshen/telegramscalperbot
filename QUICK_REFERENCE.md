# Quick Reference Card

## Installation (One-Time)

```bash
# 1. Update system
sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv

# 2. Clone repo
cd ~ && git clone https://github.com/predeshen/telegramscalperbot.git
cd telegramscalperbot

# 3. Create venv
python3 -m venv venv && source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install services
sudo bash deployment/install_services.sh
```

## Daily Operations

### Start All Scanners
```bash
sudo bash deployment/start_all_scanners.sh
```

### Stop All Scanners
```bash
sudo bash deployment/stop_all_scanners.sh
```

### Restart All Scanners
```bash
sudo bash deployment/restart_all_scanners.sh
```

### Check Status
```bash
sudo systemctl status btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

### View Logs (Real-Time)
```bash
sudo journalctl -u btc-scalp-scanner -f
```

## Individual Scanner Control

### Start Specific Scanner
```bash
sudo systemctl start btc-scalp-scanner
sudo systemctl start btc-swing-scanner
sudo systemctl start gold-scalp-scanner
sudo systemctl start gold-swing-scanner
sudo systemctl start us30-scalp-scanner
sudo systemctl start us30-swing-scanner
sudo systemctl start us100-scanner
sudo systemctl start multi-crypto-scanner
```

### Stop Specific Scanner
```bash
sudo systemctl stop btc-scalp-scanner
```

### Restart Specific Scanner
```bash
sudo systemctl restart btc-scalp-scanner
```

### Check Specific Scanner Status
```bash
sudo systemctl status btc-scalp-scanner
```

## Configuration

### Edit Configuration
```bash
nano config/unified_config.json
```

### Validate Configuration
```bash
python3 -c "from src.config_loader_unified import get_config; config = get_config(); is_valid, errors = config.validate(); print('✓ Valid' if is_valid else f'✗ Errors: {errors}')"
```

### View Configuration Summary
```bash
python3 -c "from src.config_loader_unified import get_config; config = get_config(); config.print_summary()"
```

## Monitoring

### Check All Scanners
```bash
for scanner in btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner; do
  echo -n "$scanner: "
  sudo systemctl is-active $scanner
done
```

### View Memory Usage
```bash
ps aux | grep python3 | grep -v grep
```

### View Recent Errors
```bash
sudo journalctl -u btc-scalp-scanner -n 50 | grep -i error
```

### View Last 100 Log Lines
```bash
sudo journalctl -u btc-scalp-scanner -n 100
```

## Troubleshooting

### Scanner Won't Start
```bash
# Check status
sudo systemctl status btc-scalp-scanner

# View logs
sudo journalctl -u btc-scalp-scanner -n 50

# Try manual run
source venv/bin/activate
python3 main.py
```

### Test Configuration
```bash
python3 -c "from src.config_loader_unified import get_config; config = get_config(); print('Config loaded successfully')"
```

### Test Email
```bash
python3 -c "
from src.alerter import EmailAlerter
config = {'smtp': {'server': 'mail.hashub.co.za', 'port': 465, 'user': 'alerts@hashub.co.za', 'password': 'Password@2025#!', 'from_email': 'alerts@hashub.co.za', 'to_email': 'predeshen@gmail.com', 'use_ssl': True}}
alerter = EmailAlerter(**config)
print('Email config valid')
"
```

### Test Telegram
```bash
curl -X GET "https://api.telegram.org/bot8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M/getMe"
```

## Scanner Details

| Scanner | Symbol | Timeframes | Script |
|---------|--------|-----------|--------|
| BTC Scalp | BTC/USD | 1m, 5m, 15m | main.py |
| BTC Swing | BTC/USD | 15m, 1h, 4h, 1d | main_swing.py |
| Gold Scalp | XAU/USD | 1m, 5m, 15m | xauusd_scanner/main_gold.py |
| Gold Swing | XAU/USD | 15m, 1h, 4h, 1d | xauusd_scanner/main_gold_swing.py |
| US30 Scalp | ^DJI | 1m, 5m, 15m | main_us30.py |
| US30 Swing | ^DJI | 15m, 1h, 4h | main_us30.py |
| US100 | ^NDX | 1m, 5m, 15m, 4h | main_us100.py |
| Multi-Crypto | BTC, ETH, SOL | 1m, 5m, 15m | main_multi_symbol.py |

## Credentials

- **Email**: alerts@hashub.co.za
- **Telegram Bot**: 8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M
- **Telegram Chat**: 8119046376
- **Alpha Vantage**: 66IUJDWBSTV9U220
- **Twelve Data**: a4f7101c037f4cf5949a1be62973283f

## Useful Commands

### Update Code
```bash
cd ~/telegramscalperbot
git pull origin main
```

### Activate Virtual Environment
```bash
source ~/telegramscalperbot/venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Check Python Version
```bash
python3 --version
```

### Check Installed Packages
```bash
pip list
```

### Update Requirements
```bash
pip install -r requirements.txt --upgrade
```

### Create Backup
```bash
tar -czf ~/telegramscalperbot_backup_$(date +%Y%m%d).tar.gz ~/telegramscalperbot/
```

### View System Info
```bash
uname -a
lsb_release -a
free -h
df -h
```

## Emergency Commands

### Kill All Python Processes
```bash
pkill -f python3
```

### Force Stop All Scanners
```bash
sudo systemctl stop btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

### Disable All Scanners from Auto-Start
```bash
sudo systemctl disable btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

### Re-enable All Scanners for Auto-Start
```bash
sudo systemctl enable btc-scalp-scanner btc-swing-scanner gold-scalp-scanner gold-swing-scanner us30-scalp-scanner us30-swing-scanner us100-scanner multi-crypto-scanner
```

## Documentation

- **Full Installation Guide**: `INSTALLATION_AND_STARTUP_GUIDE.md`
- **Configuration Guide**: `config/CONFIG_GUIDE.md`
- **Unified Config Summary**: `UNIFIED_CONFIG_SUMMARY.md`
- **Spec Requirements**: `.kiro/specs/scanner-system-enhancement/requirements.md`
- **Spec Design**: `.kiro/specs/scanner-system-enhancement/design.md`
- **Spec Tasks**: `.kiro/specs/scanner-system-enhancement/tasks.md`

## Support

For detailed help, see:
1. `INSTALLATION_AND_STARTUP_GUIDE.md` - Complete installation and troubleshooting
2. `config/CONFIG_GUIDE.md` - Configuration details
3. Logs: `sudo journalctl -u btc-scalp-scanner -f`
