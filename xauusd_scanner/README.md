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

## Data Source

The Gold scanner uses **Yahoo Finance Gold Futures (GC=F)** as its data source. This provides reliable, real-time market data for signal generation.

### Important Notes About Pricing

**Price Variance**: Yahoo Finance Gold Futures prices may differ slightly from spot XAU/USD prices on your broker (e.g., Vantage Markets). Typical variance is **0.1-0.5%**.

**Why Prices Differ**:
- Yahoo Finance provides Gold Futures (GC=F) data
- Your broker shows spot XAU/USD prices
- Futures and spot prices track closely but aren't identical
- Differences are due to market structure, not data quality

**Trading Implications**:
- ✅ Use scanner signals for **timing and direction**
- ✅ Always verify **exact entry price** on your broker platform before entering
- ✅ Adjust stop-loss and take-profit levels based on your broker's prices
- ⚠️ Don't blindly enter at the exact prices shown in alerts

**Example**:
```
Scanner Alert: "Entry: $2,650.50"
Your Broker:   "Current Price: $2,651.20"
Action:        Use $2,651.20 as your actual entry
```

The signal timing and direction remain valid - just use your broker's actual prices for execution.

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

## Troubleshooting

### Price Differences Between Scanner and Broker

**Problem**: "The prices in my alerts don't match my broker (Vantage Markets)"

**Explanation**: This is normal and expected. The scanner uses Yahoo Finance Gold Futures data, while your broker shows spot XAU/USD prices.

**Solution**:
1. **Don't panic** - the signal is still valid
2. **Check your broker's current price** when you receive an alert
3. **Use your broker's price** for actual trade entry
4. **Adjust levels** (stop-loss, take-profit) based on your broker's prices

**Example Scenario**:
```
Alert Received:
"🟢 XAU/USD LONG SIGNAL
Entry: $2,650.50
Stop Loss: $2,645.30
Take Profit: $2,658.70"

Your Broker Shows: $2,651.20

What To Do:
✅ Enter LONG at $2,651.20 (your broker's price)
✅ Set Stop Loss at $2,646.00 (adjusted for $0.70 difference)
✅ Set Take Profit at $2,659.40 (adjusted for $0.70 difference)
```

**Key Points**:
- The **signal direction** (LONG/SHORT) is what matters most
- The **timing** of the signal is accurate
- The **strategy reasoning** remains valid
- Only the **exact price levels** need adjustment

### Wrong Symbol in Alerts

**Problem**: "My alerts say 'BTC/USD' but I'm running the Gold scanner"

**Solution**: This has been fixed. If you still see this:
1. Stop the scanner
2. Pull the latest code updates
3. Restart the scanner
4. New alerts will show "XAU/USD"

### Data Source Questions

**Q**: Can I use a different data source?
**A**: Yes, but it requires code changes. The current Yahoo Finance integration is reliable and free.

**Q**: Why not use my broker's API directly?
**A**: Most retail brokers (including Vantage Markets) don't provide free real-time API access. Yahoo Finance is a good compromise.

**Q**: How accurate is the Yahoo Finance data?
**A**: Very accurate for signal generation. The 0.1-0.5% variance doesn't affect signal quality.

## Support
See main DEPLOYMENT_GUIDE.md for full details.
