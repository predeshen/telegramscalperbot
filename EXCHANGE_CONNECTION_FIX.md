# Exchange Connection Fix - "Failed to connect to exchange"

## Problem
The BTC Scalp Scanner was configured to use `"exchange": "hybrid"` in the config, but `main.py` was trying to initialize a regular `MarketDataClient` which uses CCXT. CCXT doesn't recognize "hybrid" as a valid exchange, causing the "Failed to connect to exchange" error.

## Root Cause
In `main.py`, the code was doing:
```python
self.market_client = MarketDataClient(
    exchange_name=self.config.exchange.name,  # This was "hybrid"
    symbol=self.config.exchange.symbol,
    timeframes=self.config.exchange.timeframes,
    buffer_size=500
)
```

When `exchange_name="hybrid"`, CCXT throws an error because it's not a real exchange.

## Solution Applied
Modified `main.py` to detect when the exchange is "hybrid" and use `HybridDataClient` instead:

```python
# Use HybridDataClient for hybrid exchange, otherwise use MarketDataClient
if self.config.exchange.name == 'hybrid':
    from src.hybrid_data_client import HybridDataClient
    
    # Get data provider keys from config
    alpha_vantage_key = None
    twelve_data_key = None
    preferred_provider = None
    
    if hasattr(self.config, 'data_providers'):
        alpha_vantage_key = getattr(self.config.data_providers, 'alpha_vantage_key', None)
        twelve_data_key = getattr(self.config.data_providers, 'twelve_data_key', None)
        preferred_provider = getattr(self.config.data_providers, 'preferred_provider', None)
    
    self.market_client = HybridDataClient(
        symbol=self.config.exchange.symbol,
        timeframes=self.config.exchange.timeframes,
        buffer_size=500,
        alpha_vantage_key=alpha_vantage_key,
        twelve_data_key=twelve_data_key,
        preferred_provider=preferred_provider
    )
    logger.info("Using HybridDataClient for multi-provider support")
else:
    self.market_client = MarketDataClient(
        exchange_name=self.config.exchange.name,
        symbol=self.config.exchange.symbol,
        timeframes=self.config.exchange.timeframes,
        buffer_size=500
    )
```

## Files Modified
1. **main.py** - Added hybrid client detection and initialization
2. **src/config_loader.py** - Added `DataProvidersConfig` dataclass to handle API keys

## How HybridDataClient Works
The `HybridDataClient` automatically selects the best data provider based on:
- Asset type (BTC, US30, XAU)
- Available API keys
- Provider priority list

For BTC, the priority is:
1. **yfinance** (primary - free, unlimited, real-time)
2. kraken (via CCXT)
3. twelve_data (if API key provided)
4. alpha_vantage (if API key provided)

## Testing
Run the test to verify the fix:
```bash
python test_hybrid_fix.py
```

Expected output:
```
✓ Config loaded successfully
✓ HybridDataClient initialized
✓ Connected successfully
✓ Fetched 10 candles
✓ All tests passed!
```

## Restarting Scanners
To restart the BTC Scalp Scanner with the fix:

**Windows:**
```bash
restart_btc_scalp.bat
```

**Or manually:**
```bash
python main.py
```

## Checking Scanner Status
To check if scanners are running and view recent errors:
```bash
python check_scanner_status.py
```

## Current Configuration
Your `config/config.json` has:
- Exchange: `hybrid`
- Symbol: `BTC/USD`
- Timeframes: `1m, 15m, 4h`
- Data providers: Alpha Vantage and Twelve Data keys configured
- Preferred provider: Auto (will use yfinance for BTC)

## What Happens Now
When you start the BTC Scalp Scanner:
1. It detects `exchange: "hybrid"` in config
2. Initializes `HybridDataClient` instead of `MarketDataClient`
3. `HybridDataClient` selects yfinance as the best provider for BTC
4. Connects to Yahoo Finance (free, unlimited, real-time data)
5. Scanner runs normally without connection errors

## Verification
After starting the scanner, check the log:
```bash
type logs\scanner.log | findstr /C:"Using" /C:"Connected"
```

You should see:
```
Using HybridDataClient for multi-provider support
Using yfinance for BTC/USD (ticker: BTC-USD)
Successfully connected to Yahoo Finance for BTC-USD
```

## Alternative: Use Direct Exchange
If you prefer to use a specific exchange instead of hybrid mode, you can change the config:

**Option 1: Use yfinance directly**
```json
"exchange": {
  "name": "yfinance",
  "symbol": "BTC-USD",
  "timeframes": ["1m", "15m", "4h"]
}
```

**Option 2: Use Kraken via CCXT**
```json
"exchange": {
  "name": "kraken",
  "symbol": "BTC/USD",
  "timeframes": ["1m", "15m", "4h"]
}
```

But the hybrid mode is recommended as it provides automatic fallback if one provider fails.
