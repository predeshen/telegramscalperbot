# Multi-Symbol Scanner Setup Guide

## Overview

The Multi-Symbol Scanner allows you to scan multiple cryptocurrencies and FX pairs simultaneously with advanced Smart Money Concepts (SMC) detection including FVG and NWOG signals.

## Quick Start

### 1. Installation

```bash
# Clone repository
cd BTCUSDScanner

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Choose a configuration file based on your trading style:

- `config/multi_crypto_scalp.json` - BTC, ETH, SOL (1m, 5m, 15m)
- `config/multi_crypto_swing.json` - BTC, ETH (15m, 1h, 4h, 1d) with FVG
- `config/multi_fx_scalp.json` - EUR/USD, GBP/USD (5m, 15m, 1h)
- `config/multi_mixed.json` - Mixed crypto and FX

### 3. Start Scanner

**Linux/Mac:**
```bash
./start_multi_crypto_scalp.sh
```

**Windows:**
```cmd
start_multi_crypto_scalp.bat
```

## Configuration Guide

### Symbol Configuration

Each symbol requires these fields:

```json
{
  "BTC-USD": {
    "enabled": true,
    "asset_type": "crypto",
    "display_name": "Bitcoin",
    "emoji": "₿",
    "timeframes": ["1m", "5m", "15m"],
    "signal_rules": {
      "volume_spike_threshold": 0.8,
      "rsi_min": 30,
      "rsi_max": 70,
      "stop_loss_atr_multiplier": 1.5,
      "take_profit_atr_multiplier": 2.0,
      "min_confluence_factors": 4,
      "min_confidence_score": 4,
      "duplicate_time_window_minutes": 5,
      "duplicate_price_threshold_percent": 0.3
    },
    "exit_rules": {
      "grace_period_minutes": 5,
      "min_profit_threshold_percent": 1.0,
      "max_giveback_percent": 40,
      "min_peak_profit_for_exit": 2.0
    },
    "volatility_thresholds": {
      "min_atr_percent": 0.5,
      "max_atr_percent": 10.0
    },
    "enable_fvg": true,
    "fvg_config": {
      "min_gap_percent": 0.15
    }
  }
}
```

### Parameter Explanations

#### Signal Rules:
- `volume_spike_threshold`: Minimum volume ratio (0.8 = 80% of average)
- `rsi_min/max`: RSI range for valid signals (30-70 typical)
- `stop_loss_atr_multiplier`: Stop loss distance in ATR units
- `take_profit_atr_multiplier`: Take profit distance in ATR units
- `min_confluence_factors`: Minimum indicators that must align
- `duplicate_time_window_minutes`: Suppress duplicates within this window

#### Exit Rules:
- `grace_period_minutes`: Wait time before evaluating exits (5-10 min recommended)
- `min_profit_threshold_percent`: Minimum profit for exit signals (1% crypto, 0.3% FX)
- `max_giveback_percent`: Max profit giveback before exit (40% typical)
- `min_peak_profit_for_exit`: Minimum peak profit required (2% typical)

#### Advanced Features:
- `enable_fvg`: Enable Fair Value Gap detection
- `enable_nwog`: Enable New Week Opening Gap detection (indices only)

### Asset-Specific Recommendations

**Crypto (BTC, ETH):**
- Grace period: 5-10 minutes
- Min profit: 1.0-1.5%
- Volume threshold: 0.8-1.0x
- ATR multipliers: 1.5-2.0x

**Altcoins (SOL, AVAX):**
- Grace period: 5 minutes
- Min profit: 1.5-2.0%
- Volume threshold: 1.0-1.2x
- ATR multipliers: 2.0-2.5x

**FX Pairs:**
- Grace period: 5-10 minutes
- Min profit: 0.3-0.5%
- Volume threshold: 1.2-1.5x
- ATR multipliers: 1.2-1.5x

**Indices (US30, Nasdaq):**
- Grace period: 10-15 minutes
- Min profit: 0.5-1.0%
- Enable NWOG: true
- Enable FVG: true

## Advanced Features

### Fair Value Gap (FVG) Detection

FVG detects institutional supply/demand zones:

```json
"enable_fvg": true,
"fvg_config": {
  "min_gap_percent": 0.15
}
```

**How it works:**
1. Detects gaps on 4h/1d where candles don't overlap
2. Monitors price re-entry into gap zones
3. Requires lower timeframe confirmation (1h/15m structure shift)
4. Generates signals with institutional targets

**Best for:** Swing trading, higher timeframes

### New Week Opening Gap (NWOG) Detection

NWOG detects weekly institutional levels:

```json
"enable_nwog": true,
"nwog_config": {
  "min_gap_percent": 0.1,
  "max_age_weeks": 4
}
```

**How it works:**
1. Identifies gap between Friday close and Monday open
2. Tracks zone as key level
3. Detects price rejection at zone
4. Counts respect occurrences

**Best for:** Indices (US30, Nasdaq, S&P500), weekly trading

## Troubleshooting

### No Signals Received

1. **Check configuration:**
   ```bash
   python -c "from src.asset_config_manager import AssetConfigManager; config = AssetConfigManager('config/multi_crypto_scalp.json'); print(config.get_config_summary())"
   ```

2. **Verify symbols enabled:**
   - Check `"enabled": true` in config
   - Verify symbol format (BTC-USD for Yahoo Finance)

3. **Check signal rules:**
   - Lower `min_confluence_factors` (try 3 instead of 4)
   - Widen RSI range (20-80 instead of 30-70)
   - Lower volume threshold (0.5 instead of 0.8)

### Connection Errors

1. **Yahoo Finance issues:**
   - Check internet connection
   - Verify symbol format
   - Try different symbol (test with BTC-USD)

2. **Rate limiting:**
   - Increase `polling_interval_seconds` (60-120)
   - Reduce number of symbols
   - Stagger scanner startups

### Too Many Signals

1. **Increase filtering:**
   - Raise `min_confluence_factors` (5 instead of 4)
   - Narrow RSI range (35-65 instead of 30-70)
   - Increase `duplicate_time_window_minutes` (10-15)

2. **Stricter exit rules:**
   - Increase `grace_period_minutes` (10 instead of 5)
   - Raise `min_profit_threshold_percent`

### Premature Exit Signals

1. **Adjust exit rules:**
   - Increase `grace_period_minutes` (10-15)
   - Raise `min_peak_profit_for_exit` (3.0 instead of 2.0)
   - Increase `max_giveback_percent` (50 instead of 40)

2. **Check current implementation:**
   - Grace period: 5 minutes (configurable)
   - No exits on negative P&L
   - Minimum profit thresholds enforced

## Command-Line Options

```bash
# Specify custom config
python main_multi_symbol.py --config config/my_custom.json

# Set log level
python main_multi_symbol.py --log-level DEBUG

# Both options
python main_multi_symbol.py --config config/multi_fx_scalp.json --log-level INFO
```

## Monitoring

### View Statistics

The scanner logs statistics every 60 seconds:
- Active scanners
- Total signals detected
- Signals sent vs suppressed
- Active trades

### Log Files

- `logs/multi_symbol_scanner.log` - Main scanner log
- Individual symbol logs (if configured)

### Telegram Alerts

Configure in `main_multi_symbol.py`:
```python
telegram_bot_token = "YOUR_BOT_TOKEN"
telegram_chat_id = "YOUR_CHAT_ID"
```

## Best Practices

1. **Start with one symbol** - Test configuration before adding more
2. **Use appropriate timeframes** - Scalp (1m-15m), Swing (15m-1d)
3. **Monitor for 24 hours** - Verify signal quality before live trading
4. **Adjust parameters** - Fine-tune based on market conditions
5. **Enable FVG for swing** - Better signals on higher timeframes
6. **Use NWOG for indices** - Excellent for US30, Nasdaq
7. **Respect grace periods** - Prevents premature exits
8. **Check logs regularly** - Monitor for errors or issues

## Migration from Single-Symbol Scanner

1. **Backup current config:**
   ```bash
   cp config/config.json config/config_backup.json
   ```

2. **Create multi-symbol config:**
   - Use `config/multi_crypto_scalp.json` as template
   - Add your symbols with appropriate parameters

3. **Test side-by-side:**
   - Run old scanner: `./start_btc_scalp.bat`
   - Run new scanner: `./start_multi_crypto_scalp.bat`
   - Compare signal quality

4. **Migrate gradually:**
   - Start with 1-2 symbols
   - Add more as you verify performance
   - Adjust parameters based on results

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration with validation tool
3. Test with minimal config (1 symbol, 1 timeframe)
4. Check GitHub issues for similar problems

## Examples

### Crypto Day Trading
```bash
./start_multi_crypto_scalp.sh
# Scans: BTC, ETH, SOL
# Timeframes: 1m, 5m, 15m
# Features: Volume spikes, EMA crossovers
```

### Crypto Swing Trading
```bash
./start_multi_crypto_swing.sh
# Scans: BTC, ETH
# Timeframes: 15m, 1h, 4h, 1d
# Features: FVG detection, trend alignment
```

### FX Scalping
```bash
./start_multi_fx_scalp.sh
# Scans: EUR/USD, GBP/USD
# Timeframes: 5m, 15m, 1h
# Features: Session filtering, tight stops
```

### Mixed Portfolio
```bash
./start_multi_mixed.sh
# Scans: BTC, ETH, EUR/USD
# Timeframes: 15m, 1h, 4h
# Features: Diversified signals
```
