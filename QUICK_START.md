# 🚀 Quick Start Guide

## Get Running in 2 Minutes

### Step 1: Configure Telegram (1 minute)

1. Open Telegram app
2. Search for `@userinfobot`
3. Send any message to the bot
4. Copy the number it shows (your chat ID)
5. Open `.env` file in project root
6. Replace `your_chat_id_here` with your chat ID
7. Save the file

Example `.env` file:
```
TELEGRAM_BOT_TOKEN=8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M
TELEGRAM_CHAT_ID=123456789
```

### Step 2: Start Scanners (30 seconds)

**Windows:**
```cmd
start_all_scanners.bat
```

**Linux:**
```bash
./start_all_scanners.sh
```

### Step 3: Verify It's Working (30 seconds)

✅ Check Telegram - You should receive a startup message
✅ Check console windows - Should show "Scanner is now running"
✅ Check logs folder - Files should be updating
✅ Wait for signals - Will appear when market conditions are met

---

## That's It! 🎉

Your scanners are now running and will:
- ✅ Calculate indicators correctly (no more NaN)
- ✅ Detect signals when market setups occur
- ✅ Send Telegram alerts for all signals
- ✅ Log everything to Excel files

---

## What You'll See

### Console Windows (6 total)
- BTC Scalping Scanner (1m/5m)
- BTC Swing Scanner (15m/1h/4h/1d)
- Gold Scalping Scanner (1m/5m)
- Gold Swing Scanner (1h/4h/1d)
- US30 Scalping Scanner (5m/15m)
- US30 Swing Scanner (4h/1d)

### Telegram Messages
- 🟢 Scanner started
- 🚀 LONG signal detected
- 📉 SHORT signal detected
- 💰 Trade updates
- 🔴 Scanner stopped

### Log Files (in `logs/` folder)
- scanner.log - BTC scalping
- scanner_swing.log - BTC swing
- gold_scanner.log - Gold scalping
- gold_swing_scanner.log - Gold swing
- us30_scalp_scanner.log - US30 scalping
- us30_swing_scanner.log - US30 swing

### Excel Reports (in `excell/` folder)
- btc_swing_scans.xlsx
- xauusd_scalp_scans.xlsx
- xauusd_swing_scans.xlsx
- us30_swing_scans.xlsx

---

## Common Commands

### Windows

```cmd
REM Start all scanners
start_all_scanners.bat

REM Start individual scanner
start_btc_scalp.bat
start_gold_swing.bat

REM Stop all scanners
stop_all_scanners.bat

REM Or press Ctrl+C in each window
```

### Linux

```bash
# Start all scanners
./start_all_scanners.sh

# View logs
tail -f logs/scanner.log
tail -f logs/gold_scanner.log

# Stop all scanners
./stop_all_scanners.sh

# Or press Ctrl+C in each terminal
```

---

## Troubleshooting

### No Telegram Messages?
- Check your chat ID is correct in .env
- Make sure you messaged @userinfobot first
- Verify no extra spaces in .env file

### Scanners Not Starting?
- Check Python is installed: `python --version`
- Make sure you're in project root directory
- Check console for error messages

### No Signals Detected?
- This is normal if market has no valid setups
- Check Excel files to see indicator values
- Enable debug mode to see why signals aren't detected
- Wait for market conditions to align

---

## Need More Help?

📖 **Detailed Guides:**
- `WINDOWS_SETUP.md` - Complete Windows guide
- `TELEGRAM_SETUP.md` - Telegram configuration
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `FINAL_STATUS.md` - Complete status report

🔧 **Troubleshooting:**
- Check logs in `logs/` directory
- Review Excel output in `excell/` directory
- Enable debug mode for detailed logging

---

## What's Fixed

The scanners were detecting 0 signals despite clear market setups. This has been fixed:

✅ **Before:** NaN indicators, insufficient data, no validation
✅ **After:** Valid indicators, 500 candles, comprehensive validation

**The signal detection issues are now resolved!** 🎉

---

**Ready to trade? Start your scanners now!** 🚀
