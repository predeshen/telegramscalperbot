# XAU/USD Gold Scalping Scanner

## Overview
Session-aware Gold trading scanner with 3 strategies, news calendar integration, and spread monitoring.

## Features
- **Session Management**: Asian/London/NY session detection
- **Asian Range Tracking**: Automatic range detection and breakout trading
- **News Calendar**: Auto-pause 30min before high-impact news
- **Spread Monitoring**: Pause when spread > 15 pips
- **Key Level Tracking**: Psychological levels, daily/weekly highs/lows
- **3 Trading Strategies**:
  1. Asian Range Breakout
  2. EMA Cloud Breakout
  3. Mean Reversion

## Quick Start

```bash
# Start Gold scanner
python xauusd_scanner/main_gold.py

# Or use unified startup
./start_all_scanners.sh
```

## Configuration
Edit `xauusd_scanner/config_gold.json`

## News Events
Update weekly: `python -m xauusd_scanner.news_updater weekly`

## Documentation
- NEWS_EVENTS_GUIDE.md - Managing economic calendar
- DEPLOYMENT_GUIDE.md - Full deployment instructions

## Trading Sessions (GMT)
- Asian: 00:00-08:00 (Range tracking)
- London: 08:00-16:00 (Breakout trading)
- NY: 13:00-22:00 (Trend continuation)
- Overlap: 13:00-16:00 (Highest volatility)

## Strategies

### 1. Asian Range Breakout
- Trades breakouts of Asian session range
- Best during London open
- Tight stops, 1.5x ATR targets

### 2. EMA Cloud Breakout
- Trend following with EMA alignment
- Active during London/NY
- 1.2x ATR stops, 1.5x ATR targets

### 3. Mean Reversion
- Reversals when overextended
- RSI extremes + reversal candles
- Target VWAP (mean)

## Support
See main DEPLOYMENT_GUIDE.md for full details.
