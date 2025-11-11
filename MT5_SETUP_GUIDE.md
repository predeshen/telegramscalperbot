# MT5 Real-Time Data Setup Guide

## Your MT5 Accounts

### HFM Account
- **Account**: 54653113
- **Server**: HFMarketsSA-Live2 Server
- **Password**: 239D8cc2#
- **Leverage**: 1:1000

### Vantage Account
- **Account**: 19002423
- **Server**: VantageInternational-Live 10
- **Password**: 239D8cc2#

## Setup Steps

### 1. Make Sure MT5 Terminal is Running

**IMPORTANT**: The MT5 terminal application must be running for the Python API to work.

1. Open MetaTrader 5 application
2. Log in to one of your accounts (HFM or Vantage)
3. Keep the terminal running in the background

### 2. Test MT5 Connection

Once MT5 terminal is running and logged in:

```bash
python test_mt5_connection.py
```

This will:
- ✓ Connect to your MT5 terminal
- ✓ Show available symbols (XAUUSD, US30, BTCUSD, etc.)
- ✓ Fetch real-time data
- ✓ Verify data freshness

### 3. Update Config

Add MT5 settings to your `config/config.json`:

```json
{
  "mt5": {
    "enabled": true,
    "account": 54653113,
    "password": "239D8cc2#",
    "server": "HFMarketsSA-Live2 Server"
  }
}
```

### 4. Use Hybrid Client

The hybrid client will automatically use MT5 for forex/indices:

```python
from src.hybrid_data_client import HybridDataClient

# For US30 or XAU/USD - uses MT5 (real-time from broker)
client = HybridDataClient(
    symbol='US30/USD',
    timeframes=['5m'],
    buffer_size=100,
    mt5_account=54653113,
    mt5_password='239D8cc2#',
    mt5_server='HFMarketsSA-Live2 Server',
    use_mt5=True
)

client.connect()
data = client.get_latest_candles('5m', 100)
```

## Why MT5 is Better

### Current Problem (yfinance)
- ❌ 2+ hours delay
- ❌ Markets appear closed when they're open
- ❌ No signals generated

### With MT5
- ✅ **TRUE real-time data** (0-5 second delay)
- ✅ Direct from your broker
- ✅ Works 24/7 for all your symbols
- ✅ No API keys needed
- ✅ No rate limits

## Symbol Names in MT5

Your broker may use slightly different symbol names:

| Our Name | MT5 Name (typical) |
|----------|-------------------|
| US30/USD | US30 or US30Cash or USTEC |
| XAU/USD | XAUUSD or GOLD |
| BTC/USD | BTCUSD or Bitcoin |

The test script will show you exactly which symbols are available in your MT5 terminal.

## Troubleshooting

### "MT5 initialize() failed"
- **Solution**: Make sure MT5 terminal application is running
- Open MT5, log in, then run the test again

### "Not logged in to any account"
- **Solution**: Log in to MT5 terminal manually first
- Or provide account credentials in the code

### "Symbol not found"
- **Solution**: Run `test_mt5_connection.py` to see available symbols
- Use the exact symbol name from your broker

### "No data received"
- **Solution**: Check if markets are open
- US30: Mon-Fri 9:30 AM - 4:00 PM ET
- XAU/USD: Almost 24/5 (check broker's trading hours)

## Next Steps

1. ✅ **Open MT5 terminal** and log in
2. ✅ **Run test**: `python test_mt5_connection.py`
3. ✅ **Note available symbols** from the test output
4. ✅ **Update your scanner** to use HybridDataClient with MT5
5. ✅ **Start getting real-time signals!**

## Expected Results

Once MT5 is connected, you'll see:

```
Latest candle:
  Time: 2025-11-11 20:17:23
  Close: $4120.50
  Volume: 1250
  Age: 2 seconds
  ✅ REAL-TIME DATA!
```

This is TRUE real-time data - exactly what you see in your MT5 terminal!

## Security Note

Your MT5 password is stored in the code. For production:
1. Use environment variables
2. Or store in a secure config file
3. Never commit passwords to git

```python
import os
mt5_password = os.getenv('MT5_PASSWORD', '239D8cc2#')
```
