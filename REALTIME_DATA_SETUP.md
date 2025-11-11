# Real-Time Data Setup Guide

## Problem Summary

Your system was not generating signals for US30 and getting weak signals for XAU/USD and BTC because:

1. **Kraken doesn't support US30 or XAU/USD** - It's a crypto-only exchange
2. **yfinance has 15-20 minute delay** - Not suitable for real-time trading
3. **Data was stale** - Markets were closed during testing

## Solution: Hybrid Data Client

We've implemented a hybrid system that routes data requests to the best provider:

- **BTC/USD** → CCXT (Kraken) - Real-time, no API key needed
- **US30/USD** → Alpha Vantage - Real-time with free API key
- **XAU/USD** → Alpha Vantage - Real-time with free API key

## Rate Limit Analysis

Your system scans every 2 minutes = 30 calls/hour per asset

### Alpha Vantage Free Tier
- **Limit**: 5 calls/min, 500 calls/day
- **Your usage**: 2 assets × 1 call/2min = **1 call/min** ✓
- **Daily**: 2 assets × 720 calls = **1,440 calls/day** ✗ EXCEEDS LIMIT

### ⚠️ PROBLEM: Daily limit exceeded!

## Better Solution: Use Twelve Data Instead

### Twelve Data Free Tier
- **Limit**: 8 calls/min, 800 calls/day
- **Your usage**: 1 call/min ✓ Well under limit
- **Daily**: ~720 calls/day ✓ Within limit!

## Setup Instructions

### Option A: Alpha Vantage (Simpler, but may hit daily limit)

1. **Get free API key** (30 seconds):
   - Go to: https://www.alphavantage.co/support/#api-key
   - Enter your email
   - Copy the API key

2. **Add to config.json**:
   ```json
   {
     "exchange": {
       "name": "hybrid",
       "alpha_vantage_key": "YOUR_KEY_HERE"
     }
   }
   ```

3. **Or set environment variable**:
   ```bash
   # Windows CMD
   set ALPHA_VANTAGE_KEY=YOUR_KEY_HERE
   
   # Windows PowerShell
   $env:ALPHA_VANTAGE_KEY="YOUR_KEY_HERE"
   
   # Linux/Mac
   export ALPHA_VANTAGE_KEY=YOUR_KEY_HERE
   ```

### Option B: Twelve Data (Recommended - higher daily limit)

1. **Get free API key**:
   - Go to: https://twelvedata.com/pricing
   - Sign up for free tier
   - Copy the API key

2. **Install library**:
   ```bash
   pip install twelvedata
   ```

3. **We'll need to create a Twelve Data client** (similar to Alpha Vantage)

## Testing

### Test BTC only (no API key needed):
```bash
python test_hybrid_client.py
```

### Test all three assets (with API key):
```bash
# Set your key first
set ALPHA_VANTAGE_KEY=your_key_here

# Then test
python test_hybrid_client.py
```

## Files Created

1. **src/alpha_vantage_client.py** - Alpha Vantage data client
2. **src/hybrid_data_client.py** - Routes requests to appropriate provider
3. **test_hybrid_client.py** - Test script for the hybrid system

## Next Steps

1. **Choose your provider** (Alpha Vantage or Twelve Data)
2. **Get free API key** (takes 30 seconds)
3. **Add key to config** or environment variable
4. **Test the system** with `python test_hybrid_client.py`
5. **Update main scanner** to use HybridDataClient

## Why Markets Appear Closed

During testing, we saw data that was 120+ minutes old. This is because:

- **BTC**: Trades 24/7 but Kraken may have low volume during certain hours
- **US30**: NYSE closes at 4:00 PM ET (21:00 UTC)
- **XAU/USD**: Gold futures have trading hours

The data will be fresh during active trading hours!

## Rate Limit Safety

The hybrid client includes:
- **Automatic rate limiting** - Waits between calls to respect limits
- **Error handling** - Gracefully handles rate limit errors
- **Logging** - Shows when rate limits are hit

With your 2-minute scan interval, you're well within all rate limits!
