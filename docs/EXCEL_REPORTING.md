# Excel Reporting and Email Notifications

## Overview

All trading scanners now support Excel-based logging and automated email reporting. This feature helps you:
- Monitor scanner activity and verify it's running correctly
- Review historical scan results with full indicator data
- Receive hourly email reports with Excel attachments
- Get an initial verification report within 5 minutes of startup
- Debug missing alerts or incorrect scanner behavior

## Configuration

### Enabling Excel Reporting

Add the following section to your scanner's config file:

```json
{
  "excel_reporting": {
    "enabled": true,
    "excel_file_path": "logs/scanner_scans.xlsx",
    "report_interval_seconds": 3600,
    "initial_report_delay_seconds": 300,
    "smtp": {
      "server": "mail.hashub.co.za",
      "port": 465,
      "user": "alerts@hashub.co.za",
      "password": "your_password_here",
      "from_email": "alerts@hashub.co.za",
      "to_email": "your_email@example.com",
      "use_ssl": true
    }
  }
}
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enabled` | boolean | false | Enable/disable Excel reporting |
| `excel_file_path` | string | - | Path to Excel file (relative to project root) |
| `report_interval_seconds` | integer | 3600 | Interval between email reports (1 hour) |
| `initial_report_delay_seconds` | integer | 300 | Delay before first report (5 minutes) |
| `smtp.server` | string | - | SMTP server address |
| `smtp.port` | integer | - | SMTP port (465 for SSL, 587 for TLS) |
| `smtp.user` | string | - | SMTP username |
| `smtp.password` | string | - | SMTP password (set to "DISABLED" to disable) |
| `smtp.from_email` | string | - | Sender email address |
| `smtp.to_email` | string | - | Recipient email address |
| `smtp.use_ssl` | boolean | true | Use SSL/TLS for SMTP connection |

### Disabling Excel Reporting

To disable Excel reporting, either:
1. Set `"enabled": false` in the config
2. Set `"password": "DISABLED"` in the SMTP config
3. Remove the `excel_reporting` section entirely

## Excel File Format

### Columns

Each scan result is logged as a row with the following columns:

| Column | Description |
|--------|-------------|
| `scan_id` | Sequential scan number |
| `timestamp` | Scan timestamp (ISO 8601 format) |
| `scanner` | Scanner name (e.g., "BTC-Scalp", "XAUUSD-Swing-London") |
| `symbol` | Trading symbol (e.g., "BTC/USDT", "XAUUSD") |
| `timeframe` | Timeframe (e.g., "1m", "5m", "1h") |
| `price` | Current price |
| `volume` | Current volume |
| `ema_9` | EMA 9 indicator value |
| `ema_21` | EMA 21 indicator value |
| `ema_50` | EMA 50 indicator value |
| `ema_100` | EMA 100 indicator value |
| `ema_200` | EMA 200 indicator value |
| `rsi` | RSI indicator value |
| `atr` | ATR indicator value |
| `volume_ma` | Volume moving average |
| `vwap` | VWAP (if applicable) |
| `stoch_k` | Stochastic K (if applicable) |
| `stoch_d` | Stochastic D (if applicable) |
| `signal_detected` | TRUE if signal detected, FALSE otherwise |
| `signal_type` | "LONG" or "SHORT" (if signal detected) |
| `signal_entry` | Entry price (if signal detected) |
| `signal_sl` | Stop loss price (if signal detected) |
| `signal_tp` | Take profit price (if signal detected) |
| `signal_rr` | Risk/reward ratio (if signal detected) |
| `signal_strategy` | Strategy name (if signal detected) |

### File Management

- Excel files are created automatically if they don't exist
- New scan results are appended to existing files
- Files include auto-filters on the header row
- Column widths are auto-sized for readability

## Email Reports

### Initial Report

Within 5 minutes of starting a scanner, you'll receive an initial verification email with:
- Scanner name and start time
- Current scan statistics
- Excel file attachment with all scans so far

This helps you quickly verify the scanner is running correctly.

### Hourly Reports

Every hour (or at your configured interval), you'll receive an email with:
- Scanner name and report period
- Total scans performed
- Number of signals detected
- Signal breakdown (LONG vs SHORT)
- Excel file attachment with all scans since last report

### Email Format

**Subject:** `[Scanner Name] Hourly Report - 2024-11-03 14:30`

**Body:**
```
Scanner Activity Report
=======================

Scanner: BTC Scalp Scanner
Report Period: 2024-11-03 13:30:00 to 2024-11-03 14:30:00 UTC

Summary:
- Total Scans: 360
- Signals Detected: 3
- Signal Breakdown: LONG: 2, SHORT: 1

Attached: btc_scalp_scans.xlsx
```

## Scanner-Specific Details

### BTC Scalp Scanner (main.py)
- **Excel File:** `logs/btc_scalp_scans.xlsx`
- **Scanner Name:** "BTC-Scalp"
- **Scan Frequency:** Every 10 seconds (polling mode)
- **Timeframes:** 1m, 5m

### BTC Swing Scanner (main_swing.py)
- **Excel File:** `logs/btc_swing_scans.xlsx`
- **Scanner Name:** "BTC-Swing"
- **Scan Frequency:** Every 60 seconds
- **Timeframes:** 15m, 1h, 4h, 1d

### XAUUSD Scalp Scanner (xauusd_scanner/main_gold.py)
- **Excel File:** `logs/xauusd_scalp_scans.xlsx`
- **Scanner Name:** "XAUUSD-Scalp-{Session}" (includes session info)
- **Scan Frequency:** Variable (10-30 seconds based on session)
- **Timeframes:** 1m, 5m
- **Special:** Includes session information (Asian/London/NY)

### XAUUSD Swing Scanner (xauusd_scanner/main_gold_swing.py)
- **Excel File:** `logs/xauusd_swing_scans.xlsx`
- **Scanner Name:** "XAUUSD-Swing-{Session}"
- **Scan Frequency:** Variable based on timeframe
- **Timeframes:** 1h, 4h, 1d

### US30 Scalp Scanner (us30_scanner/main_us30_scalp.py)
- **Excel File:** `logs/us30_scalp_scans.xlsx`
- **Scanner Name:** "US30-Scalp"
- **Scan Frequency:** Every 60 seconds
- **Timeframes:** 5m, 15m
- **Special:** Includes stochastic indicators

### US30 Swing Scanner (us30_scanner/main_us30_swing.py)
- **Excel File:** `logs/us30_swing_scans.xlsx`
- **Scanner Name:** "US30-Swing"
- **Scan Frequency:** Variable based on timeframe
- **Timeframes:** 4h, 1d

## Troubleshooting

### No Excel File Created

**Problem:** Scanner runs but no Excel file is created.

**Solutions:**
1. Check that `excel_reporting.enabled` is `true`
2. Verify SMTP password is not "DISABLED"
3. Check logs for Excel initialization errors
4. Ensure the logs directory exists and is writable

### No Email Reports Received

**Problem:** Excel file is created but no emails are sent.

**Solutions:**
1. Verify SMTP credentials are correct
2. Check SMTP server and port settings
3. Ensure firewall allows outbound SMTP connections
4. Check spam/junk folder
5. Review logs for email sending errors

### Excel File Locked Error

**Problem:** "Excel file locked" warnings in logs.

**Solutions:**
1. Close Excel if you have the file open
2. The scanner will retry automatically (3 attempts)
3. If persistent, restart the scanner

### Missing Indicator Columns

**Problem:** Some indicator columns are empty.

**Solutions:**
1. This is normal if the scanner doesn't calculate that indicator
2. Different scanners use different indicators
3. Check the scanner's indicator configuration

### Large Excel Files

**Problem:** Excel files grow very large over time.

**Solutions:**
1. Archive old Excel files periodically
2. Reduce scan frequency if possible
3. Consider implementing daily file rotation (future enhancement)

## Best Practices

1. **Monitor Initial Report:** Always check the initial report within 5 minutes to verify the scanner is working
2. **Review Hourly Reports:** Check hourly reports to ensure signals aren't being missed
3. **Archive Old Files:** Periodically archive Excel files to prevent disk space issues
4. **Test SMTP First:** Test your SMTP settings with a simple email before enabling reporting
5. **Use Dedicated Email:** Consider using a dedicated email address for scanner reports
6. **Check Spam Filters:** Add the sender email to your whitelist to prevent reports going to spam

## Security Considerations

1. **Protect Config Files:** Config files contain SMTP passwords - keep them secure
2. **Use App Passwords:** For Gmail/Outlook, use app-specific passwords instead of your main password
3. **Limit Email Access:** Only send reports to trusted email addresses
4. **Secure Excel Files:** Excel files contain trading data - store them securely

## Performance Impact

Excel reporting has minimal performance impact:
- Excel writes take <10ms per scan
- Email sending happens in background threads
- No impact on signal detection or alerting
- Scanner continues running even if Excel/email fails

## Future Enhancements

Planned improvements:
- Daily Excel file rotation
- Compression of old Excel files
- Cloud storage integration (Google Drive, Dropbox)
- Web dashboard for viewing Excel data
- Advanced analytics in email reports
- Multi-recipient support
- Slack/Discord integration
