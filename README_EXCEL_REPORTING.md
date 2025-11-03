# Excel Reporting Feature - Quick Start

## What's New?

All your trading scanners now automatically log every scan to Excel and email you hourly reports! 🎉

## Quick Setup (3 Steps)

### 1. Enable SMTP Password

Edit your scanner's config file and update the SMTP password:

```json
"excel_reporting": {
  "enabled": true,
  "smtp": {
    "password": "your_actual_password_here"  // Change from "DISABLED"
  }
}
```

### 2. Install Dependency

```bash
pip install openpyxl>=3.1.0
```

### 3. Run Your Scanner

```bash
python main.py
```

That's it! You'll receive:
- ✅ Initial verification email within 5 minutes
- ✅ Hourly reports with Excel attachments
- ✅ Full scan history in `logs/*.xlsx` files

## What Gets Logged?

Every scan includes:
- Timestamp, price, volume
- All indicator values (EMA, RSI, ATR, etc.)
- Signal detection (LONG/SHORT)
- Entry, stop loss, take profit prices
- Risk/reward ratios

## Email Reports Include:

- Total scans performed
- Signals detected (LONG vs SHORT breakdown)
- Time period covered
- Excel file attachment with all data

## Config Files Updated

All scanners now have Excel reporting configured:
- ✅ `config/config.json` (BTC Scalp)
- ✅ `config/config_multitime.json` (BTC Swing)
- ✅ `xauusd_scanner/config_gold.json` (XAUUSD Scalp)
- ✅ `xauusd_scanner/config_gold_swing.json` (XAUUSD Swing)
- ✅ `us30_scanner/config_us30_scalp.json` (US30 Scalp)
- ✅ `us30_scanner/config_us30_swing.json` (US30 Swing)

## Excel Files Location

- BTC Scalp: `logs/btc_scalp_scans.xlsx`
- BTC Swing: `logs/btc_swing_scans.xlsx`
- XAUUSD Scalp: `logs/xauusd_scalp_scans.xlsx`
- XAUUSD Swing: `logs/xauusd_swing_scans.xlsx`
- US30 Scalp: `logs/us30_scalp_scans.xlsx`
- US30 Swing: `logs/us30_swing_scans.xlsx`

## Troubleshooting

**No emails?**
- Check SMTP password is not "DISABLED"
- Verify SMTP credentials are correct
- Check spam/junk folder

**No Excel file?**
- Ensure `enabled: true` in config
- Check logs directory exists
- Review scanner logs for errors

## Full Documentation

See `docs/EXCEL_REPORTING.md` for complete documentation including:
- Detailed configuration options
- Excel file format reference
- Scanner-specific details
- Troubleshooting guide
- Best practices

## Disable Feature

To disable Excel reporting:
1. Set `"enabled": false` in config, OR
2. Set `"password": "DISABLED"` in SMTP config

## Support

If you encounter issues:
1. Check the scanner logs
2. Review `docs/EXCEL_REPORTING.md`
3. Share the Excel file for debugging

---

**Note:** Excel reporting runs in the background and won't affect scanner performance or signal detection. If Excel/email fails, the scanner continues running normally.
