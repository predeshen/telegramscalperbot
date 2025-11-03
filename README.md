# BTC Scalping Scanner

Real-time BTC/USD scalping signal detection system with email and Telegram alerts. Monitors 1-minute and 5-minute charts using confluence-based technical analysis to identify high-probability trading opportunities.

## Features

- **Real-time Market Data**: WebSocket streaming from Binance for sub-second latency
- **Confluence-Based Signals**: Multiple technical indicators must align (EMA crossovers, VWAP, RSI, volume spikes)
- **Dual Alert System**: Email (SMTP) and Telegram bot notifications
- **Risk Management**: Automatic stop-loss and take-profit calculation using ATR
- **Duplicate Prevention**: Smart filtering to avoid redundant signals
- **Health Monitoring**: Uptime tracking, error logging, and performance metrics
- **Production Ready**: Systemd service, automatic reconnection, graceful shutdown

## Technical Indicators

### Confluence Factors (All Must Align)
1. **Trend**: EMA(9) crosses EMA(21)
2. **Bias**: Price relative to VWAP (session)
3. **Momentum**: RSI(6) in valid range (30-70)
4. **Volume**: 1.5x average volume spike
5. **Higher Timeframe**: Price relative to EMA(50)

### Signal Types
- **LONG**: Bullish confluence detected
- **SHORT**: Bearish confluence detected

## System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+)
- **Python**: 3.9 or higher
- **RAM**: 1 GB minimum
- **Disk**: 10 GB (for logs)
- **Network**: Outbound internet access

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd btc-scalping-scanner
```

### 2. Run Installation Script

```bash
sudo bash deployment/install.sh
```

This will:
- Install Python dependencies
- Create system user `btc-scanner`
- Set up directories (`/opt/btc-scanner`, `/etc/btc-scanner`, `/var/log/btc-scanner`)
- Install systemd service
- Copy configuration template

### 3. Configure Settings

Edit the configuration file:

```bash
sudo nano /etc/btc-scanner/config.json
```

#### SMTP Configuration (Required)

```json
{
  "smtp": {
    "server": "mail.hashub.co.za",
    "port": 465,
    "user": "alerts@hashub.co.za",
    "password": "your_password_here",
    "from_email": "alerts@hashub.co.za",
    "to_email": "your_email@example.com",
    "use_ssl": true
  }
}
```

#### Telegram Configuration (Optional)

To enable Telegram alerts:

1. **Create a Telegram Bot**:
   - Open Telegram and talk to [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow instructions
   - Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get Your Chat ID**:
   - Talk to [@userinfobot](https://t.me/userinfobot)
   - Copy your chat ID (numeric value)

3. **Update Config**:

```json
{
  "telegram": {
    "enabled": true,
    "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
    "chat_id": "your_chat_id"
  }
}
```

### 4. Start Service

```bash
# Enable auto-start on boot
sudo systemctl enable btc-scanner

# Start the service
sudo systemctl start btc-scanner

# Check status
sudo systemctl status btc-scanner
```

## Usage

### View Live Logs

```bash
# Follow systemd journal
sudo journalctl -u btc-scanner -f

# Follow application log file
sudo tail -f /var/log/btc-scanner/scanner.log
```

### Service Management

```bash
# Start
sudo systemctl start btc-scanner

# Stop
sudo systemctl stop btc-scanner

# Restart
sudo systemctl restart btc-scanner

# Status
sudo systemctl status btc-scanner

# Disable auto-start
sudo systemctl disable btc-scanner
```

### Configuration Changes

After editing `/etc/btc-scanner/config.json`, restart the service:

```bash
sudo systemctl restart btc-scanner
```

## Signal Alert Format

### Email Example

```
🟢 BTC/USD Scalping Signal Detected

Signal Type: LONG
Timeframe: 5m
Entry Price: $65,432.50
Stop Loss: $65,200.00 (-0.36%)
Take Profit: $65,665.00 (+0.36%)
Risk/Reward: 1:1.00

Market Context:
- ATR(14): $232.50
- Market Bias: BULLISH
- Confidence: 5/5 factors

Indicators:
- EMA(9): $65,450.00
- EMA(21): $65,380.00
- EMA(50): $65,100.00
- VWAP: $65,300.00
- RSI(6): 55.3
- Volume: 1,234,567 (1.75x avg)

Timestamp: 2025-11-02 14:35:00 UTC
```

### Telegram Example

```
🟢 BTC/USD LONG Signal

Entry: $65,432.50
Stop Loss: $65,200.00 (-0.36%)
Take Profit: $65,665.00 (+0.36%)
R:R: 1:1.00

Market: BULLISH | TF: 5m
ATR: $232.50 | Confidence: 5/5

Indicators:
EMA9: $65,450.00 | EMA21: $65,380.00
VWAP: $65,300.00 | RSI: 55.3
Volume: 1.75x avg

14:35:00 UTC
```

## Configuration Reference

### Exchange Settings

```json
{
  "exchange": {
    "name": "binance",
    "symbol": "BTC/USDT",
    "timeframes": ["1m", "5m"]
  }
}
```

### Indicator Parameters

```json
{
  "indicators": {
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 50,
    "atr_period": 14,
    "rsi_period": 6,
    "volume_ma_period": 20
  }
}
```

### Signal Rules

```json
{
  "signal_rules": {
    "volume_spike_threshold": 1.5,
    "rsi_min": 30,
    "rsi_max": 70,
    "stop_loss_atr_multiplier": 1.5,
    "take_profit_atr_multiplier": 1.0,
    "duplicate_time_window_minutes": 5,
    "duplicate_price_threshold_percent": 0.3
  }
}
```

### Logging

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/scanner.log",
    "rotation": "daily",
    "retention_days": 7
  }
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u btc-scanner -n 50

# Check configuration syntax
python3 -c "import json; json.load(open('/etc/btc-scanner/config.json'))"

# Check permissions
ls -la /opt/btc-scanner
ls -la /var/log/btc-scanner
```

### No Signals Received

- **Check market conditions**: Signals require specific confluence conditions
- **Verify WebSocket connection**: Check logs for "WebSocket connection established"
- **Check timeframe data**: Logs should show "Loaded 1m data" and "Loaded 5m data"
- **Test email/Telegram**: Check SMTP credentials and Telegram bot token

### Email Delivery Fails

```bash
# Test SMTP connection
python3 -c "
import smtplib
server = smtplib.SMTP_SSL('mail.hashub.co.za', 465, timeout=10)
server.login('alerts@hashub.co.za', 'your_password')
print('SMTP connection successful')
server.quit()
"
```

### Telegram Not Working

- Verify bot token is correct (from @BotFather)
- Verify chat ID is correct (from @userinfobot)
- Check that `python-telegram-bot` is installed: `pip3 list | grep telegram`
- Start a conversation with your bot first (send `/start`)

### High Memory Usage

- Reduce buffer size in code (default 200 candles per timeframe)
- Reduce log retention days
- Check for memory leaks in logs

### WebSocket Disconnects

- Normal behavior - auto-reconnects with exponential backoff
- Check network stability
- Verify firewall allows outbound WebSocket connections (port 9443)

## Performance

- **Latency**: < 2 seconds from market data to signal generation
- **Memory**: < 200 MB typical usage
- **CPU**: < 10% on single core
- **Network**: ~1 KB/s average (WebSocket data)

## Security

- Configuration file permissions: `600` (owner read/write only)
- Service runs as dedicated user `btc-scanner` (no root)
- No inbound network ports (outbound only)
- SSL/TLS for SMTP and WebSocket connections
- Sensitive credentials can be stored in environment variables

### Using Environment Variables

Instead of storing passwords in config file:

```bash
# Create environment file
sudo nano /etc/btc-scanner/env

# Add credentials
SMTP_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# Update systemd service
sudo nano /etc/systemd/system/btc-scanner.service

# Add under [Service]
EnvironmentFile=/etc/btc-scanner/env

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart btc-scanner
```

## Development

### Local Testing

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run locally
python3 main.py
```

### Running Tests

```bash
# Install test dependencies
pip3 install pytest pytest-asyncio pytest-mock

# Run tests
pytest tests/
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BTC Scalping Scanner                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Market     │─────▶│  Indicator   │─────▶│  Signal   │ │
│  │   Data       │      │  Calculator  │      │  Detector │ │
│  │   Client     │      └──────────────┘      └─────┬─────┘ │
│  └──────┬───────┘                                   │       │
│         │                                            │       │
│         │                                            ▼       │
│         │                                    ┌───────────┐  │
│         │                                    │   Multi   │  │
│         │                                    │  Alerter  │  │
│         │                                    └─────┬─────┘  │
│         │                                          │        │
│         │                                    ┌─────┴─────┐  │
│         │                                    │           │  │
│         │                                ┌───▼───┐ ┌─────▼──┐
│         │                                │ Email │ │Telegram│
│         │                                └───────┘ └────────┘
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │   Health     │                                           │
│  │   Monitor    │                                           │
│  └──────────────┘                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Disclaimer

This software is for educational and informational purposes only. Trading cryptocurrencies carries risk. Always do your own research and never trade with money you cannot afford to lose. The authors are not responsible for any financial losses incurred while using this software.
