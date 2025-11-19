# Unified Configuration Guide

## Overview

The `unified_config.json` file contains all configuration data and credentials for the Trading Scanner System. This is the single source of truth for all scanner settings.

## Configuration Structure

### 1. Application Settings
```json
"application": {
  "name": "Trading Scanner System",
  "version": "2.0.0",
  "environment": "production"
}
```

### 2. Data Providers
Configure data sources with fallback logic:
- **Primary**: Binance (crypto)
- **Fallback**: Twelve Data, Alpha Vantage, MT5
- **Credentials**: API keys for each provider
- **Freshness**: 300 seconds (5 minutes)
- **Retry**: Exponential backoff (1s, 2s, 4s)

### 3. Communication Channels

#### SMTP (Email)
- Server: mail.hashub.co.za
- Port: 465 (SSL)
- User: alerts@hashub.co.za
- Password: Password@2025#!
- To: predeshen@gmail.com

#### Telegram
- Bot Token: 8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M
- Chat ID: 8119046376

### 4. Indicators
Standard technical indicators used across all scanners:
- EMA: 9 (fast), 21 (slow), 50 (trend)
- ATR: 14 period
- RSI: 6 period
- Volume MA: 20 period

### 5. Signal Rules
Global signal detection parameters:
- Volume spike threshold: 1.3x
- RSI range: 25-75
- ADX minimum: 15
- Risk/Reward minimum: 1.2

### 6. Asset-Specific Configuration

Each asset has custom parameters:

**Crypto (BTC, ETH, SOL)**
- ADX threshold: 15
- Volume thresholds: 1.3-1.5x
- Trading hours: 24/7

**Commodities (Gold/XAUUSD)**
- ADX threshold: 15
- Volume thresholds: 1.4-1.6x
- Trading hours: London, New York

**Indices (US30, US100)**
- ADX threshold: 18-20
- Volume thresholds: 1.3-1.5x
- Trading hours: New York

**Forex (EUR/USD, GBP/USD)**
- ADX threshold: 15
- Volume thresholds: 1.4-1.6x
- Trading hours: London, New York

### 7. Strategies

Enabled strategies:
- Fibonacci Retracement
- Support/Resistance Bounce
- Key Level Break/Retest
- ADX/RSI Momentum
- H4 HVG (Higher Volume Gap)
- FVG Detection (Fair Value Gap)
- NWOG Detection (New Week Old Gap)

### 8. Scanners

8 main scanners configured:
1. **BTC Scalp**: 1m, 5m, 15m timeframes
2. **BTC Swing**: 15m, 1h, 4h, 1d timeframes
3. **Gold Scalp**: 1m, 5m, 15m timeframes
4. **Gold Swing**: 15m, 1h, 4h, 1d timeframes
5. **US30 Scalp**: 1m, 5m, 15m timeframes
6. **US30 Swing**: 15m, 1h, 4h timeframes
7. **US100**: 1m, 5m, 15m, 4h timeframes
8. **Multi-Crypto**: BTC, ETH, SOL

Plus multi-symbol scanners:
- Multi-Crypto Scalp
- Multi-Crypto Swing
- Multi-FX Scalp
- Multi-Mixed

## Usage

### Loading Configuration

```python
import json

with open('config/unified_config.json', 'r') as f:
    config = json.load(f)

# Access specific settings
smtp_config = config['communication']['smtp']
btc_config = config['asset_specific']['BTC']
strategies = config['strategies']
```

### Updating Configuration

1. Edit `unified_config.json` directly
2. Restart scanners to apply changes
3. Or use hot-reload if implemented

### Environment Variables

For sensitive data, use environment variables:

```bash
export ALPHA_VANTAGE_KEY="your_key"
export TWELVE_DATA_KEY="your_key"
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_id"
export SMTP_PASSWORD="your_password"
```

## Security Notes

⚠️ **Important**: 
- Never commit credentials to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use strong passwords for email accounts
- Restrict file permissions: `chmod 600 config/unified_config.json`

## Customization

### Adding New Asset

```json
"NEW_ASSET": {
  "enabled": true,
  "display_name": "Asset Name",
  "emoji": "🔷",
  "asset_type": "crypto|forex|index|commodity",
  "adx_threshold": 15,
  "volume_thresholds": {...},
  "rsi_range": {"min": 25, "max": 75},
  "trading_hours": ["London", "NewYork"]
}
```

### Adding New Strategy

```json
"new_strategy": {
  "enabled": true,
  "scanners": ["btc_scalp", "btc_swing"],
  "params": {
    "param1": value1,
    "param2": value2
  }
}
```

### Adding New Scanner

```json
"new_scanner": {
  "enabled": true,
  "symbol": "SYMBOL",
  "timeframes": ["1m", "5m"],
  "polling_interval_seconds": 30,
  "scanner_type": "scalp|swing|mixed",
  "strategies": ["strategy1", "strategy2"]
}
```

## Validation

Validate configuration before deployment:

```python
import json
from jsonschema import validate

with open('config/unified_config.json', 'r') as f:
    config = json.load(f)

# Check required fields
required_fields = ['application', 'data_providers', 'communication', 'scanners']
for field in required_fields:
    assert field in config, f"Missing required field: {field}"

print("✓ Configuration is valid")
```

## Troubleshooting

### Scanner not starting
- Check scanner is enabled in config
- Verify symbol format matches data provider
- Check timeframes are supported

### No signals detected
- Verify strategies are enabled
- Check signal rules thresholds
- Review diagnostics logs

### Email alerts not sending
- Verify SMTP credentials
- Check firewall allows port 465
- Test with: `telnet mail.hashub.co.za 465`

### Telegram alerts not sending
- Verify bot token is correct
- Check chat ID is valid
- Ensure bot has permission to send messages

## Migration from Old Config

If migrating from individual config files:

1. Backup old configs: `cp config/*.json config/backup/`
2. Use `unified_config.json` as primary
3. Keep old configs for reference
4. Update application to load from unified config
5. Test all scanners before production

## Support

For configuration issues:
- Check logs in `logs/` directory
- Review this guide
- Check individual scanner logs
- Contact support with config excerpt (remove credentials)
