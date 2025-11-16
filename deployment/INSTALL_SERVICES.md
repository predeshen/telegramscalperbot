# Installing Multi-Symbol Scanner Services

This guide explains how to install and manage the systemd services for the multi-symbol scanners.

## Prerequisites

1. Ubuntu/Debian Linux system
2. Python 3.9+ installed
3. Virtual environment set up at `/home/ubuntu/trading-bot/venv`
4. Telegram credentials configured in `.env` file

## Available Services

### Multi-Symbol Scanners (New)
- `multi-crypto-scalp-scanner.service` - BTC, ETH, SOL on 1m/5m/15m
- `multi-crypto-swing-scanner.service` - BTC, ETH on 15m/1h/4h/1d
- `multi-fx-scalp-scanner.service` - EUR/USD, GBP/USD on 5m/15m/1h
- `multi-mixed-scanner.service` - BTC, ETH, EUR/USD on 15m/1h/4h

### Legacy Scanners (Old)
- `btc-scalp-scanner.service`
- `btc-swing-scanner.service`
- `gold-scalp-scanner.service`
- `gold-swing-scanner.service`
- `us30-scalp-scanner.service`
- `us30-swing-scanner.service`
- `us30-momentum-scanner.service`

## Installation Steps

### 1. Update Service Files

Edit each service file and update the paths if needed:
- `User=ubuntu` (change to your username)
- `WorkingDirectory=/home/ubuntu/trading-bot` (change to your path)

### 2. Copy Service Files

```bash
# Copy multi-symbol scanner services
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload
```

### 3. Enable Services (Auto-start on boot)

```bash
# Enable multi-symbol scanners
sudo systemctl enable multi-crypto-scalp-scanner
sudo systemctl enable multi-crypto-swing-scanner
sudo systemctl enable multi-fx-scalp-scanner
sudo systemctl enable multi-mixed-scanner

# Or enable all at once
sudo systemctl enable multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner
```

### 4. Start Services

```bash
# Start individual service
sudo systemctl start multi-crypto-scalp-scanner

# Or start all multi-symbol scanners
sudo systemctl start multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner
```

### 5. Check Status

```bash
# Check individual service
sudo systemctl status multi-crypto-scalp-scanner

# Check all services
sudo systemctl status multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner
```

## Managing Services

### View Logs

```bash
# View logs for a specific scanner
sudo journalctl -u multi-crypto-scalp-scanner -f

# View logs from the log file
tail -f /home/ubuntu/trading-bot/logs/multi_crypto_scalp.log
```

### Restart Services

```bash
# Restart individual service
sudo systemctl restart multi-crypto-scalp-scanner

# Or use the convenience script
./restart_scanners.sh
```

### Stop Services

```bash
# Stop individual service
sudo systemctl stop multi-crypto-scalp-scanner

# Stop all
sudo systemctl stop multi-crypto-scalp-scanner multi-crypto-swing-scanner multi-fx-scalp-scanner multi-mixed-scanner
```

### Disable Services (Prevent auto-start)

```bash
sudo systemctl disable multi-crypto-scalp-scanner
```

## Configuration

Each scanner uses a JSON configuration file in the `config/` directory:

- `config/multi_crypto_scalp.json` - Crypto scalping configuration
- `config/multi_crypto_swing.json` - Crypto swing trading configuration
- `config/multi_fx_scalp.json` - FX scalping configuration
- `config/multi_mixed.json` - Mixed asset configuration

Edit these files to:
- Enable/disable specific symbols
- Adjust timeframes
- Modify signal rules
- Configure exit rules

After changing configuration, restart the service:
```bash
sudo systemctl restart multi-crypto-scalp-scanner
```

## Troubleshooting

### Service won't start

1. Check logs:
   ```bash
   sudo journalctl -u multi-crypto-scalp-scanner -n 50
   ```

2. Verify Python path:
   ```bash
   /home/ubuntu/trading-bot/venv/bin/python3 --version
   ```

3. Check Telegram credentials:
   ```bash
   cat /home/ubuntu/trading-bot/.env
   ```

4. Test manually:
   ```bash
   cd /home/ubuntu/trading-bot
   source venv/bin/activate
   python3 main_multi_symbol.py --config config/multi_crypto_scalp.json
   ```

### Service keeps restarting

Check for errors in the log file:
```bash
tail -100 /home/ubuntu/trading-bot/logs/multi_crypto_scalp.log
```

Common issues:
- Missing Telegram credentials
- Invalid configuration file
- Network connectivity issues
- Insufficient permissions

## Health Monitoring

Each scanner creates a health check file:
```bash
cat /home/ubuntu/trading-bot/logs/scanner_health.json
```

This file contains:
- Uptime
- Signal counts
- Scanner status
- Error counts

## Migration from Legacy Scanners

If you're migrating from legacy single-symbol scanners:

1. Stop legacy scanners:
   ```bash
   sudo systemctl stop btc-scalp-scanner btc-swing-scanner
   ```

2. Start multi-symbol scanners:
   ```bash
   sudo systemctl start multi-crypto-scalp-scanner multi-crypto-swing-scanner
   ```

3. Disable legacy scanners (optional):
   ```bash
   sudo systemctl disable btc-scalp-scanner btc-swing-scanner
   ```

The multi-symbol scanners provide:
- Better resource efficiency (one process for multiple symbols)
- Centralized signal filtering
- Cross-symbol conflict resolution
- Unified trade tracking
- Better performance monitoring
