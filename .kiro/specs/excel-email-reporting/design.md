# Design Document

## Overview

This feature adds a centralized Excel logging and email reporting system that can be integrated into all existing scanners (BTC scalp, BTC swing, US30 scalp, US30 swing, XAUUSD scalp, XAUUSD swing). The system will:

1. Log every scan cycle result to an Excel file with full context
2. Send email reports with the Excel file attached at configurable intervals
3. Send an initial report within 5 minutes of startup for quick verification
4. Be fully configurable via each scanner's config file

The design follows a modular approach with a reusable `ExcelReporter` class that can be instantiated in any scanner's main loop.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Scanner Main Loop                        │
│  (main.py, main_swing.py, main_gold.py, etc.)              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ instantiates & calls
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    ExcelReporter                             │
│  - log_scan_result()                                        │
│  - send_email_report()                                      │
│  - schedule_reports()                                       │
└────────┬───────────────────────────────┬────────────────────┘
         │                               │
         │ writes to                     │ sends via
         ▼                               ▼
┌──────────────────┐           ┌──────────────────────┐
│  Excel File      │           │  Email Service       │
│  (.xlsx)         │           │  (SMTP)              │
└──────────────────┘           └──────────────────────┘
```

### Integration Points

Each scanner will:
1. Load `excel_reporting` config section
2. Instantiate `ExcelReporter` if enabled
3. Call `reporter.log_scan_result()` after each scan cycle
4. Let the reporter handle scheduling and sending emails automatically

## Components and Interfaces

### 1. ExcelReporter Class

**Location:** `src/excel_reporter.py`

**Responsibilities:**
- Append scan results to Excel file
- Schedule and send email reports
- Handle file I/O errors gracefully
- Manage email sending with retry logic

**Interface:**

```python
class ExcelReporter:
    def __init__(
        self,
        excel_file_path: str,
        smtp_config: dict,
        report_interval_seconds: int = 3600,
        initial_report_delay_seconds: int = 300,
        scanner_name: str = "Scanner"
    ):
        """
        Initialize Excel reporter.
        
        Args:
            excel_file_path: Path to Excel file
            smtp_config: SMTP configuration dict
            report_interval_seconds: Interval between reports (default: 1 hour)
            initial_report_delay_seconds: Delay before first report (default: 5 min)
            scanner_name: Name of scanner for email subject
        """
        
    def log_scan_result(self, scan_data: dict) -> bool:
        """
        Append scan result to Excel file.
        
        Args:
            scan_data: Dictionary containing scan result data
            
        Returns:
            True if successful, False otherwise
        """
        
    def start(self) -> None:
        """Start the reporter (schedules email reports)."""
        
    def stop(self) -> None:
        """Stop the reporter gracefully."""
```

**Scan Data Format:**

```python
scan_data = {
    'timestamp': datetime,
    'scanner': str,           # e.g., "BTC-Scalp", "XAUUSD-Swing"
    'symbol': str,            # e.g., "BTC/USDT", "XAUUSD"
    'timeframe': str,         # e.g., "1m", "15m"
    'price': float,
    'volume': float,
    'indicators': {           # All calculated indicators
        'ema_9': float,
        'ema_21': float,
        'rsi': float,
        'atr': float,
        # ... etc
    },
    'signal_detected': bool,
    'signal_type': str,       # "LONG", "SHORT", or None
    'signal_details': dict    # Full signal object if detected
}
```

### 2. Email Service Integration

**Uses existing SMTP configuration** from each scanner's config file.

**Email Format:**

- **Subject:** `[Scanner Name] Hourly Report - [Date/Time]`
- **Body (HTML):**
  ```
  Scanner Activity Report
  =======================
  
  Scanner: [Name]
  Report Period: [Start] to [End]
  
  Summary:
  - Total Scans: [count]
  - Signals Detected: [count]
  - Signal Types: [LONG: X, SHORT: Y]
  - Average Price: [value]
  
  Attached: scan_results_[timestamp].xlsx
  
  [Initial report includes startup notification]
  ```
- **Attachment:** Excel file with all scan results

### 3. Configuration Schema

**Added to each scanner's config file:**

```json
{
  "excel_reporting": {
    "enabled": true,
    "excel_file_path": "logs/btc_scalp_scans.xlsx",
    "report_interval_seconds": 3600,
    "initial_report_delay_seconds": 300,
    "smtp": {
      "server": "mail.hashub.co.za",
      "port": 465,
      "user": "alerts@hashub.co.za",
      "password": "your_password",
      "from_email": "alerts@hashub.co.za",
      "to_email": "predeshen@gmail.com",
      "use_ssl": true
    }
  }
}
```

**Note:** SMTP config can reference the existing `smtp` section or have its own dedicated config.

## Data Models

### Excel File Structure

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| scan_id | int | Sequential scan number |
| timestamp | datetime | ISO 8601 format |
| scanner | str | Scanner name |
| symbol | str | Trading symbol |
| timeframe | str | Timeframe |
| price | float | Current price |
| volume | float | Current volume |
| ema_9 | float | EMA 9 value |
| ema_21 | float | EMA 21 value |
| ema_50 | float | EMA 50 value |
| rsi | float | RSI value |
| atr | float | ATR value |
| volume_ma | float | Volume MA |
| vwap | float | VWAP (if applicable) |
| stoch_k | float | Stochastic K (if applicable) |
| stoch_d | float | Stochastic D (if applicable) |
| signal_detected | bool | True/False |
| signal_type | str | "LONG", "SHORT", or empty |
| signal_entry | float | Entry price (if signal) |
| signal_sl | float | Stop loss (if signal) |
| signal_tp | float | Take profit (if signal) |
| signal_rr | float | Risk/reward ratio (if signal) |
| signal_strategy | str | Strategy name (if signal) |

**File Management:**
- Create new file if doesn't exist
- Append to existing file
- Use `openpyxl` library for Excel operations
- Auto-format columns with appropriate widths
- Add filters to header row

## Error Handling

### Excel File Errors

1. **File doesn't exist:** Create new file with headers
2. **File locked/in use:** Log warning, retry after 5 seconds (max 3 retries)
3. **Disk full:** Log error, continue scanner operation
4. **Permission denied:** Log error, disable Excel logging for session

### Email Errors

1. **SMTP connection failed:** Log error, retry next interval
2. **Authentication failed:** Log error, disable email reports
3. **Attachment too large:** Compress or split file
4. **Network timeout:** Retry with exponential backoff (max 3 attempts)

**Critical Rule:** Excel/email failures must NEVER crash the scanner. All errors are logged and operation continues.

## Testing Strategy

### Unit Tests

1. **ExcelReporter Class:**
   - Test file creation with headers
   - Test appending scan results
   - Test data formatting and types
   - Test error handling for file operations

2. **Email Functionality:**
   - Test email composition
   - Test attachment handling
   - Test SMTP connection (mocked)
   - Test retry logic

### Integration Tests

1. **Scanner Integration:**
   - Test reporter initialization from config
   - Test scan result logging in main loop
   - Test graceful shutdown

2. **End-to-End:**
   - Run scanner for 10 minutes
   - Verify Excel file contains expected rows
   - Verify initial email sent within 5 minutes
   - Verify hourly email sent (or mock time)

### Manual Testing

1. Start scanner with Excel reporting enabled
2. Verify Excel file created
3. Verify initial email received within 5 minutes
4. Let run for 1+ hours, verify hourly emails
5. Test with Excel reporting disabled
6. Test error scenarios (invalid SMTP, disk full, etc.)

## Implementation Notes

### Libraries Required

Add to `requirements.txt`:
```
openpyxl>=3.1.0
```

### Threading Considerations

- Email sending runs in background thread to avoid blocking scanner
- Use `threading.Timer` for scheduling reports
- Ensure thread-safe Excel file access (use locks if needed)

### Performance

- Excel append operations are fast (<10ms)
- Email sending happens asynchronously
- No impact on scanner's main loop performance

### Backward Compatibility

- Feature is opt-in via config
- Existing scanners work unchanged if `excel_reporting.enabled = false`
- No breaking changes to existing code

## Scanner-Specific Adaptations

### BTC Scalp Scanner (main.py)
- Log results from polling loop (every 10 seconds)
- Include 1m and 5m timeframe data

### BTC Swing Scanner (main_swing.py)
- Log results for 15m, 1h, 4h, 1d timeframes
- Include multi-timeframe context

### XAUUSD Scanners (main_gold.py, main_gold_swing.py)
- Include session information (Asian/London/NY)
- Include spread data
- Include key level proximity

### US30 Scanners (main_us30_scalp.py, main_us30_swing.py)
- Include stochastic indicator values
- Include trading hours status
- Include liquidity sweep detection data

## Deployment Considerations

1. **File Paths:** Use relative paths, create directories if needed
2. **Log Rotation:** Excel files can grow large; consider daily rotation
3. **Email Limits:** Respect SMTP rate limits (1 email/hour is safe)
4. **Disk Space:** Monitor disk usage, implement file size limits if needed
5. **Timezone:** Use UTC for all timestamps, convert in email body if needed

## Future Enhancements

1. **Dashboard:** Web dashboard to view Excel data
2. **Compression:** Compress old Excel files automatically
3. **Cloud Storage:** Upload to Google Drive/Dropbox
4. **Advanced Analytics:** Add summary statistics to emails
5. **Multi-recipient:** Support multiple email recipients
6. **Slack/Discord:** Alternative notification channels
