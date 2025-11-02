# Implementation Plan

- [x] 1. Set up project structure and configuration management


  - Create directory structure: `/src`, `/config`, `/tests`, `/logs`
  - Implement configuration loader that reads JSON config file and validates schema
  - Create `config.json` template with all parameters from design (exchange, indicators, SMTP, logging)
  - Add `.env` support for sensitive credentials as alternative to config file
  - _Requirements: 7.5_



- [ ] 2. Implement Market Data Client
  - [ ] 2.1 Create MarketDataClient class with CCXT integration
    - Initialize CCXT exchange instance (Binance)
    - Implement `connect()` method to establish exchange connection
    - Implement `get_latest_candles()` to fetch historical candlesticks via REST API


    - Create thread-safe deque buffers (maxlen=200) for 1m and 5m timeframes
    - _Requirements: 1.1, 1.3_
  
  - [ ] 2.2 Implement WebSocket streaming for real-time data
    - Connect to Binance WebSocket API for BTC/USDT kline streams (1m and 5m)

    - Parse incoming WebSocket messages and update candlestick buffers
    - Ensure updates complete within 2 seconds of exchange timestamp
    - Add threading.Lock for thread-safe buffer access
    - _Requirements: 1.2_
  
  - [ ] 2.3 Add reconnection logic with exponential backoff
    - Implement `reconnect()` method with retry attempts (1s, 2s, 4s, 8s, 16s)


    - Handle WebSocket disconnect events and trigger reconnection
    - Log all connection events (connect, disconnect, reconnect attempts)
    - Refetch missing candles after reconnection to maintain continuity
    - _Requirements: 1.4, 1.5_

- [x] 3. Implement Indicator Calculator

  - [ ] 3.1 Create IndicatorCalculator class with core indicator methods
    - Implement `calculate_ema()` using pandas ewm with adjust=False
    - Implement `calculate_vwap()` with daily session reset logic
    - Implement `calculate_atr()` using true range and Wilder smoothing
    - Implement `calculate_rsi()` using Wilder smoothing on gains/losses
    - Implement `calculate_volume_ma()` using simple moving average
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_


  
  - [ ] 3.2 Create unified indicator calculation pipeline
    - Implement `calculate_all_indicators()` that applies all indicators to DataFrame
    - Add caching mechanism to avoid recalculating unchanged data

    - Handle edge cases (insufficient data, NaN values, division by zero)
    - Return DataFrame with all indicator columns appended
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 4. Implement Signal Detector with confluence logic
  - [ ] 4.1 Create Signal dataclass and SignalDetector class
    - Define Signal dataclass with all fields (timestamp, type, entry, SL, TP, ATR, etc.)
    - Initialize SignalDetector with configurable parameters from config

    - Create signal history deque (maxlen=50) for duplicate tracking
    - _Requirements: 3.5, 4.5, 6.4_
  
  - [ ] 4.2 Implement bullish confluence detection
    - Check price > VWAP condition
    - Detect EMA(9) cross above EMA(21) in last 2 candles
    - Verify volume > 1.5× volume MA(20)
    - Validate RSI(6) between 30 and 70

    - Check price > EMA(50) for bullish bias
    - Calculate entry, stop-loss (entry - 1.5×ATR), take-profit (entry + 1.0×ATR)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 4.3 Implement bearish confluence detection
    - Check price < VWAP condition

    - Detect EMA(9) cross below EMA(21) in last 2 candles
    - Verify volume > 1.5× volume MA(20)
    - Validate RSI(6) between 30 and 70
    - Check price < EMA(50) for bearish bias
    - Calculate entry, stop-loss (entry + 1.5×ATR), take-profit (entry - 1.0×ATR)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  


  - [ ] 4.4 Implement duplicate signal prevention
    - Check if same signal type was generated within 5 minutes
    - Check if price moved > 0.3% from last signal entry price
    - Block duplicate signals that don't meet time or price threshold
    - Clean expired signals (>30 minutes old) from history buffer

    - _Requirements: 6.1, 6.2, 6.3, 6.5_
  
  - [ ] 4.5 Calculate risk management metrics
    - Calculate risk-reward ratio: (TP - entry) / (entry - SL)
    - Calculate stop-loss distance as percentage of entry
    - Determine market bias (bullish/bearish/neutral) from EMA positioning

    - Calculate confidence score (3-5) based on confluence factors met
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 5. Implement Email Alerter
  - [ ] 5.1 Create EmailAlerter class with SMTP integration
    - Initialize with SMTP config (server, port, credentials, SSL)


    - Implement `send_signal_alert()` method using smtplib.SMTP_SSL
    - Format email with subject, body template from design document
    - Include all signal details (entry, SL, TP, indicators, timestamp)
    - _Requirements: 5.1, 5.3_
  

  - [ ] 5.2 Add retry logic and error handling
    - Implement 3 retry attempts with 5-second delays between attempts
    - Set 10-second timeout per SMTP connection attempt
    - Log all email send attempts (success and failure)
    - Handle authentication errors, connection timeouts, and network failures
    - _Requirements: 5.2, 5.4, 5.5_
  
  - [x] 5.3 Implement error alert emails for critical failures

    - Create `send_error_alert()` method for system errors
    - Format error email with exception details, timestamp, and context
    - Send to administrator email address from config
    - _Requirements: 7.3_

- [-] 6. Implement Logger and Health Monitor

  - [ ] 6.1 Set up structured logging with rotation
    - Configure Python logging module with INFO level
    - Create rotating file handler (daily rotation, 7-day retention)
    - Set log format: `[{timestamp}] [{level}] [{component}] {message}`
    - Create log directory `/var/log/btc-scanner/` if it doesn't exist
    - _Requirements: 7.2_
  
  - [ ] 6.2 Create HealthMonitor class for metrics tracking
    - Track uptime (start timestamp)
    - Count total signals generated (separate long/short counters)
    - Record last data update timestamp
    - Track connection status (connected/disconnected)
    - Count errors in last hour (rolling window)
    - Calculate email success rate
    - _Requirements: 7.4_
  
  - [ ] 6.3 Implement health status reporting
    - Create `get_health_status()` method returning current metrics
    - Create `get_metrics()` method returning dict of all tracked values
    - Log health summary every 5 minutes
    - _Requirements: 7.4_

- [ ] 7. Create main application orchestrator
  - [x] 7.1 Implement main event loop

    - Initialize all components (MarketDataClient, IndicatorCalculator, SignalDetector, EmailAlerter, HealthMonitor)
    - Connect to exchange and start WebSocket streams
    - Process incoming candles: calculate indicators → detect signals → send alerts
    - Handle graceful shutdown on SIGTERM/SIGINT
    - _Requirements: 1.1, 7.1_
  
  - [x] 7.2 Add error recovery and critical error handling

    - Wrap main loop in try-except to catch all exceptions
    - Log critical errors with full stack trace
    - Send error alert email for critical failures
    - Implement automatic restart on recoverable errors
    - Exit with non-zero code on unrecoverable errors (systemd will restart)
    - _Requirements: 7.3_
  
  - [x] 7.3 Implement graceful shutdown handler

    - Register signal handlers for SIGTERM and SIGINT
    - Close WebSocket connections cleanly
    - Flush log buffers to disk
    - Save last processed timestamp to state file
    - Exit with code 0
    - _Requirements: 7.1_

- [ ] 8. Create deployment artifacts
  - [x] 8.1 Write systemd service file


    - Create `btc-scanner.service` file with configuration from design
    - Set restart policy to `always` with 10-second delay
    - Configure service to run as dedicated user `btc-scanner`
    - Set working directory to `/opt/btc-scanner`
    - _Requirements: 7.1_
  
  - [x] 8.2 Create installation script


    - Write bash script to install Python dependencies (ccxt, pandas, pandas-ta, websocket-client)
    - Create log directory with proper permissions
    - Copy config template to `/etc/btc-scanner/config.json`
    - Copy systemd service file to `/etc/systemd/system/`
    - Create dedicated user `btc-scanner` if it doesn't exist
    - _Requirements: 7.5_
  
  - [x] 8.3 Write README with deployment instructions


    - Document system requirements (Linux, Python 3.9+, RAM, disk)
    - Provide step-by-step installation instructions
    - Explain configuration file parameters
    - Include monitoring commands (systemctl status, journalctl, tail logs)
    - Add troubleshooting section for common issues
    - _Requirements: 7.5_

- [x] 9. Create test suite


  - [ ] 9.1 Write unit tests for IndicatorCalculator
    - Test EMA calculation against known reference values
    - Test VWAP calculation with sample price/volume data
    - Test ATR calculation with various volatility scenarios
    - Test RSI calculation at boundaries (0, 50, 100)
    - Test volume MA calculation


    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 9.2 Write unit tests for SignalDetector
    - Test bullish confluence with mock data (all conditions met)
    - Test bearish confluence with mock data
    - Test duplicate detection (time window and price threshold)

    - Test edge cases (missing indicators, NaN values, insufficient data)
    - Test risk metric calculations (RR ratio, stop distance, confidence)
    - _Requirements: 3.1-3.5, 4.1-4.5, 6.1-6.5, 8.1-8.5_
  
  - [x] 9.3 Write integration test for end-to-end signal flow

    - Mock exchange WebSocket with pre-recorded BTC/USD data
    - Inject known signal setups (EMA cross + volume spike + VWAP alignment)
    - Verify signal detection and email formatting
    - Measure latency from data ingestion to signal generation
    - Mock SMTP server to verify email delivery without sending real emails
    - _Requirements: 1.1, 1.2, 5.1, 5.2_

- [ ] 10. Integration and final validation
  - [x] 10.1 Deploy to Linux VM and verify service operation

    - Run installation script on clean Ubuntu/Debian VM
    - Start systemd service and verify it runs without errors
    - Monitor logs for 1 hour to check for crashes or errors
    - Verify WebSocket connection stability
    - _Requirements: 7.1, 7.2_
  
  - [x] 10.2 Validate email delivery and formatting

    - Trigger test signal manually or wait for real signal
    - Verify email arrives at predeshen@gmail.com
    - Check email formatting matches design template
    - Verify all signal details are present and accurate
    - Test error alert email delivery
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 10.3 Test reconnection and error recovery

    - Simulate exchange downtime (block network or kill WebSocket)
    - Verify automatic reconnection with exponential backoff
    - Check that no duplicate signals are generated during reconnection
    - Verify data continuity after reconnection (no missing candles)
    - _Requirements: 1.4, 6.2, 6.3_
  
  - [x] 10.4 Verify duplicate signal prevention


    - Wait for a signal to be generated
    - Manually trigger the same setup within 5 minutes
    - Verify that duplicate signal is blocked
    - Wait for price to move >0.3% and verify new signal is allowed
    - _Requirements: 6.1, 6.2, 6.3_
