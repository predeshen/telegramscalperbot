# Windows Desktop Setup Guide

## Quick Start

### 1. Install Python
- Download Python 3.9+ from https://www.python.org/
- **Important**: Check "Add Python to PATH" during installation

### 2. Set Up Environment Variables
Create a `.env` file in the project root with your credentials:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Start All Scanners
Double-click `start_all_scanners.bat`

This will open 6 console windows:
- BTC Scalping Scanner (1m/5m)
- BTC Swing Scanner (15m/1h/4h/1d)
- Gold Scalping Scanner (1m/5m)
- Gold Swing Scanner (1h/4h/1d)
- US30 Scalping Scanner (5m/15m)
- US30 Swing Scanner (4h/1d)

### 4. Stop All Scanners
Double-click `stop_all_scanners.bat`

## Individual Scanner Control

You can also start scanners individually:

- `start_btc_scalp.bat` - Bitcoin scalping (1m/5m timeframes)
- `start_btc_swing.bat` - Bitcoin swing trading (15m/1h/4h/1d)
- `start_gold_scalp.bat` - Gold scalping (1m/5m)
- `start_gold_swing.bat` - Gold swing trading (1h/4h/1d)
- `start_us30_scalp.bat` - US30/Dow Jones scalping (5m/15m)
- `start_us30_swing.bat` - US30/Dow Jones swing (4h/1d)

## What the Batch Files Do

Each batch file automatically:
1. Checks if Python is installed
2. Creates a virtual environment (if needed)
3. Installs/updates dependencies
4. Checks for .env file
5. Starts the scanner
6. Shows real-time logs in the console

## Monitoring

### Console Windows
Each scanner runs in its own console window showing:
- Initialization messages
- Data fetching logs
- Signal detection alerts
- Error messages (if any)

### Log Files
Detailed logs are saved in the `logs/` directory:
- `logs/scanner.log` - BTC scalping
- `logs/scanner_swing.log` - BTC swing
- `logs/gold_scanner.log` - Gold scalping
- `logs/gold_swing_scanner.log` - Gold swing
- `logs/us30_scalp_scanner.log` - US30 scalping
- `logs/us30_swing_scanner.log` - US30 swing

### Excel Reports
Scan results are saved in the `excell/` directory:
- `excell/btc_swing_scans.xlsx`
- `excell/xauusd_scalp_scans.xlsx`
- `excell/xauusd_swing_scans.xlsx`
- `excell/us30_swing_scans.xlsx`

## Telegram Alerts

If configured correctly, you'll receive Telegram messages for:
- Scanner startup/shutdown
- Trading signals detected
- Trade updates (entry, stop-loss hit, take-profit hit)

## Troubleshooting

### "Python is not installed or not in PATH"
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation
- Restart Command Prompt after installation

### "WARNING: .env file not found"
- Create a `.env` file in the project root directory
- Add your Telegram credentials (see step 2 above)

### "Failed to create virtual environment"
- Make sure you have write permissions in the project directory
- Try running Command Prompt as Administrator

### Scanners Not Detecting Signals
- Check the console window for error messages
- Review log files in `logs/` directory
- Verify indicators are calculated (no NaN values in Excel output)
- Enable debug mode for detailed condition logging

### High CPU Usage
- This is normal during initialization (fetching historical data)
- CPU usage should drop to <5% per scanner after startup
- If consistently high, check for network issues or API rate limiting

## Stopping Scanners

### Method 1: Stop All (Recommended)
Double-click `stop_all_scanners.bat`

### Method 2: Individual Stop
Press `Ctrl+C` in each console window

### Method 3: Task Manager
1. Open Task Manager (Ctrl+Shift+Esc)
2. Find Python processes
3. End task for each scanner

## Tips

### Running on Startup
1. Press `Win+R`, type `shell:startup`, press Enter
2. Create a shortcut to `start_all_scanners.bat`
3. Scanners will start automatically when Windows boots

### Minimizing Console Windows
- Console windows can be minimized to taskbar
- They'll continue running in the background
- Check taskbar for window titles to identify each scanner

### Viewing Multiple Logs
Use Windows Terminal or open multiple Command Prompt windows:
```cmd
REM Window 1
tail -f logs/scanner.log

REM Window 2
tail -f logs/gold_scanner.log

REM etc.
```

Or use PowerShell:
```powershell
Get-Content logs/scanner.log -Wait -Tail 50
```

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.9 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 500MB free space
- **Internet**: Stable connection for API calls

## Performance

### Expected Resource Usage (All 6 Scanners)
- **CPU**: 10-20% total (2-3% per scanner)
- **RAM**: 1-2GB total (~200-300MB per scanner)
- **Network**: ~1-5 KB/s per scanner (polling mode)

### Optimization Tips
- Close unused scanners to save resources
- Use swing scanners only (longer timeframes = less frequent updates)
- Increase polling intervals in config files

## Getting Help

If you encounter issues:
1. Check console window for error messages
2. Review log files in `logs/` directory
3. Check Excel output for indicator values
4. Enable debug mode in scanner code
5. Verify .env file has correct credentials

## Advanced Configuration

### Changing Timeframes
Edit the config files:
- `config/config.json` - BTC scalping
- `config/config_multitime.json` - BTC swing
- `xauusd_scanner/config_gold.json` - Gold scalping
- `xauusd_scanner/config_gold_swing.json` - Gold swing
- `us30_scanner/config_us30_scalp.json` - US30 scalping
- `us30_scanner/config_us30_swing.json` - US30 swing

### Changing Polling Intervals
In config files, adjust `polling_interval_seconds`:
```json
{
  "polling_interval_seconds": 60
}
```

### Enabling Debug Mode
In scanner code, add `debug=True`:
```python
signal = signal_detector.detect_signals(candles, timeframe, debug=True)
```

## Security Notes

- Keep your `.env` file secure (never commit to Git)
- Use read-only API keys where possible
- Telegram bot token should be kept private
- Review logs regularly for suspicious activity

## Updates

To update the scanners:
1. Pull latest code from repository
2. Run `pip install -r requirements.txt` in virtual environment
3. Restart scanners

The batch files will automatically update dependencies on each start.
