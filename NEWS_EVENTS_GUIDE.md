# XAU/USD News Events Management Guide

## Overview
The Gold scanner automatically pauses trading 30 minutes before high-impact news events to avoid volatile whipsaws.

## Current Events File
Location: `xauusd_scanner/news_events.json`

## Auto-Update Options

### Option 1: Use News Updater CLI (Recommended)
```bash
# Initialize with sample events
python -m xauusd_scanner.news_updater init

# List upcoming events
python -m xauusd_scanner.news_updater list

# Add weekly recurring events (NFP, etc.)
python -m xauusd_scanner.news_updater weekly

# Clean up old events
python -m xauusd_scanner.news_updater cleanup
```

### Option 2: Manual Updates
Edit `xauusd_scanner/news_events.json` directly:

```json
{
  "events": [
    {
      "title": "US Non-Farm Payrolls",
      "datetime_gmt": "2025-11-07T13:30:00+00:00",
      "impact": "high",
      "currency": "USD",
      "description": "Monthly employment report"
    }
  ]
}
```

### Option 3: Programmatic Updates
```python
from xauusd_scanner.news_updater import NewsUpdater

updater = NewsUpdater()

# Add single event
updater.add_manual_event(
    title="FOMC Meeting",
    date_str="2025-11-06",
    time_str="19:00",  # GMT
    impact="high",
    currency="USD"
)

# Add weekly events
updater.add_weekly_events()
```

## Important Events for Gold

### High-Impact USD Events (Always Monitor)
- **Non-Farm Payrolls (NFP)** - First Friday, 13:30 GMT
- **FOMC Rate Decision** - 8 times/year, 19:00 GMT
- **FOMC Press Conference** - After rate decision, 19:30 GMT
- **CPI (Inflation)** - Monthly, 13:30 GMT
- **GDP** - Quarterly, 13:30 GMT
- **Retail Sales** - Monthly, 13:30 GMT

### Medium-Impact Events
- **Unemployment Claims** - Weekly Thursday, 13:30 GMT
- **PMI Data** - Monthly, various times
- **Consumer Confidence** - Monthly, 15:00 GMT

### Other Currencies Affecting Gold
- **ECB Rate Decision** - EUR, 12:45 GMT
- **BOE Rate Decision** - GBP, 12:00 GMT
- **RBA Rate Decision** - AUD, 03:30 GMT

## Event Sources

### Free Sources
1. **ForexFactory.com** - Best free calendar
2. **Investing.com** - Economic calendar section
3. **TradingEconomics.com** - Comprehensive data

### How to Update Weekly
1. Visit ForexFactory.com every Sunday
2. Filter for "High Impact" USD events
3. Add to `news_events.json` or use CLI
4. Run cleanup to remove old events

## Automation (Future Enhancement)

For fully automated updates, integrate with:
- **ForexFactory API** (unofficial)
- **Trading Economics API** (paid)
- **Investing.com scraper** (custom)

Example integration point in `news_calendar.py`:
```python
def fetch_from_api(self):
    # TODO: Integrate with external API
    # For now, manual updates work well
    pass
```

## Scanner Behavior

### Before News (30 min window)
- ✅ Scanner detects imminent news
- 🛑 Stops generating new signals
- 📱 Sends Telegram notification
- 📊 Continues monitoring (no trades)

### During News
- 🛑 No trading
- 👀 Watches for extreme moves
- 📈 Tracks volatility

### After News (5 min delay)
- ⏳ Waits 5 minutes for dust to settle
- ✅ Resumes normal trading
- 📱 Sends resume notification

## Maintenance Schedule

### Weekly (Recommended)
```bash
# Sunday evening
python -m xauusd_scanner.news_updater weekly
python -m xauusd_scanner.news_updater list 7
```

### Monthly
```bash
# Clean up old events
python -m xauusd_scanner.news_updater cleanup
```

## Testing

Test news pause functionality:
```python
from xauusd_scanner.news_calendar import NewsCalendar
from datetime import datetime, timedelta, timezone

calendar = NewsCalendar()

# Add test event 25 minutes from now
test_time = datetime.now(timezone.utc) + timedelta(minutes=25)
calendar.add_event(
    title="Test Event",
    datetime_gmt=test_time,
    impact="high"
)

# Check if should pause
should_pause, reason = calendar.should_pause_trading()
print(f"Should pause: {should_pause}")
print(f"Reason: {reason}")
```

## Tips

1. **Set reminders** - Update calendar every Sunday
2. **Focus on USD** - Gold is most sensitive to USD events
3. **High-impact only** - Don't pause for medium/low impact
4. **Time zones** - Always use GMT in the file
5. **Test first** - Add test event to verify pause works

## Current Events

Run this to see what's scheduled:
```bash
python -m xauusd_scanner.news_updater list 14
```

## Questions?

- Events not pausing? Check `logs/scanner_gold.log`
- Wrong timezone? Events must be in GMT
- Missing events? Run `news_updater weekly`
