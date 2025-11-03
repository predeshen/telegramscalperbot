# Implementation Plan

- [x] 1. Fix Indicator Calculator with validation and error handling


  - Add data validation before calculations (check for required columns, sufficient rows)
  - Replace silent NaN returns with explicit error raising
  - Add minimum data requirement checks for each indicator
  - Improve error logging with specific failure reasons
  - _Requirements: 1.1, 1.5, 2.1, 2.2, 2.3_



- [x] 2. Enhance Market Data Client with better data fetching

  - [x] 2.1 Increase buffer size from 200 to 500 candles for swing scanners

    - Update MarketDataClient default buffer_size parameter
    - Update all scanner initialization code to use 500 candles
    - _Requirements: 3.1, 3.4_
  

  - [x] 2.2 Fix YFinanceClient period calculation

    - Rewrite _calculate_period() method with correct time calculations
    - Add buffer to ensure sufficient data (request 20% more than needed)
    - Add logging to show calculated period vs requested candles
    - _Requirements: 3.3, 3.5_

  
  - [x] 2.3 Add data validation in get_latest_candles()

    - Validate DataFrame has required columns (open, high, low, close, volume, timestamp)
    - Check for empty DataFrames
    - Verify minimum row count
    - Log warnings for data quality issues
    - _Requirements: 2.2, 2.3, 3.4_

- [x] 3. Improve Signal Detector with indicator validation



  - [x] 3.1 Add indicator validation before signal detection

    - Create _validate_indicators() method to check for NaN values
    - Return None early if critical indicators are missing
    - Log which indicators are invalid
    - _Requirements: 1.1, 1.4, 2.1, 4.1_
  


  - [ ] 3.2 Add detailed condition logging
    - Log each confluence condition (passed/failed)
    - Log EMA alignments, RSI levels, volume ratios
    - Add debug mode flag for verbose logging
    - _Requirements: 4.2, 4.3, 4.5, 5.1, 5.2, 5.5_


  
  - [ ] 3.3 Fix bearish/bullish signal detection logic
    - Review and fix EMA crossover detection
    - Ensure volume confirmation is properly checked
    - Verify RSI range validation
    - Test with known market setups
    - _Requirements: 4.2, 4.3, 4.4_

- [ ] 4. Implement Kraken WebSocket support
  - [x] 4.1 Create KrakenWebSocketStreamer class

    - Implement WebSocket connection to Kraken API
    - Handle authentication and subscription
    - Parse candlestick data from WebSocket messages
    - _Requirements: 6.2, 6.3_
  

  - [ ] 4.2 Add reconnection logic with exponential backoff
    - Implement automatic reconnection on disconnect
    - Add exponential backoff delays (1s, 2s, 4s, 8s, 16s)
    - Log connection status changes
    - _Requirements: 6.4_

  
  - [ ] 4.3 Integrate WebSocket into MarketDataClient
    - Add use_websocket parameter to MarketDataClient
    - Start WebSocket in background thread
    - Update buffers from WebSocket callbacks
    - Fall back to REST polling if WebSocket fails
    - _Requirements: 6.2, 6.3, 6.4_


- [ ] 5. Create systemd service files for Linux deployment
  - [ ] 5.1 Create service files for all scanners
    - btc-scalp-scanner.service (main.py)
    - btc-swing-scanner.service (main_swing.py)
    - gold-scalp-scanner.service (xauusd_scanner/main_gold.py)
    - gold-swing-scanner.service (xauusd_scanner/main_gold_swing.py)
    - us30-scalp-scanner.service (us30_scanner/main_us30_scalp.py)
    - us30-swing-scanner.service (us30_scanner/main_us30_swing.py)
    - _Requirements: 6.1, 6.5, 6.6, 6.7_

  
  - [ ] 5.2 Create installation script for systemd services
    - Write install_all_services.sh script
    - Copy service files to /etc/systemd/system/
    - Create dedicated user for each scanner
    - Set up log directories with proper permissions
    - Enable services to start on boot

    - _Requirements: 6.1, 6.6, 6.7_
  
  - [ ] 5.3 Add graceful shutdown handling
    - Implement signal handlers for SIGTERM and SIGINT
    - Close WebSocket connections cleanly
    - Flush logs and Excel reports

    - Send shutdown notification via Telegram

    - _Requirements: 6.5_

- [x] 6. Create Windows batch file launchers

  - [x] 6.1 Create individual scanner batch files

    - start_btc_scalp.bat
    - start_btc_swing.bat
    - start_gold_scalp.bat
    - start_gold_swing.bat
    - start_us30_scalp.bat
    - start_us30_swing.bat
    - Each opens in separate console window with title
    - _Requirements: N/A (Windows desktop support)_
  

  - [x] 6.2 Create master start/stop batch files

    - start_all_scanners.bat - launches all scanners
    - stop_all_scanners.bat - kills all scanner processes
    - Add error handling and status messages
    - _Requirements: N/A (Windows desktop support)_


- [ ] 7. Update configuration files
  - [ ] 7.1 Add new configuration options
    - Add buffer_size parameter to exchange config
    - Add use_websocket flag for Kraken
    - Add debug_mode flag for signal detection
    - Add validation_enabled flag for data checking
    - _Requirements: 1.5, 2.1, 3.3, 4.1, 6.2_
  
  - [x] 7.2 Update all scanner config files

    - config/config.json (BTC scalp)
    - config/config_multitime.json (BTC swing)
    - xauusd_scanner/config_gold.json (Gold scalp)
    - xauusd_scanner/config_gold_swing.json (Gold swing)
    - us30_scanner/config_us30_scalp.json (US30 scalp)
    - us30_scanner/config_us30_swing.json (US30 swing)
    - _Requirements: 3.1, 3.3, 6.2_

- [x] 8. Enhance logging throughout the system

  - [ ] 8.1 Add scan result logging
    - Log every scan with current price and all indicator values
    - Log whether signal was detected or not
    - Include timeframe and scanner name
    - _Requirements: 5.1, 5.4_
  

  - [ ] 8.2 Add indicator calculation logging
    - Log when indicators produce NaN values
    - Log input data shape and reason for failure
    - Add debug logging for calculation steps
    - _Requirements: 2.3, 5.3_
  

  - [ ] 8.3 Add WebSocket event logging
    - Log connection/disconnection events
    - Log subscription confirmations
    - Log data latency warnings
    - _Requirements: 6.3, 6.4_



- [ ] 9. Update main scanner files with improvements
  - [x] 9.1 Update main.py (BTC scalp scanner)

    - Increase buffer size to 500
    - Add signal handler for graceful shutdown
    - Add indicator validation before signal detection
    - Improve error handling in main loop
    - _Requirements: 1.1, 2.1, 3.1, 6.5_
  

  - [x] 9.2 Update main_swing.py (BTC swing scanner)

    - Increase buffer size to 500
    - Add signal handler for graceful shutdown
    - Add indicator validation before signal detection
    - Improve error handling in main loop
    - _Requirements: 1.1, 2.1, 3.1, 6.5_
  

  - [ ] 9.3 Update xauusd_scanner/main_gold.py (Gold scalp)
    - Fix YFinance period calculation
    - Increase buffer size to 500
    - Add signal handler for graceful shutdown
    - Add indicator validation before signal detection
    - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.3, 6.5_

  
  - [ ] 9.4 Update xauusd_scanner/main_gold_swing.py (Gold swing)
    - Fix YFinance period calculation
    - Increase buffer size to 500
    - Add signal handler for graceful shutdown
    - Add indicator validation before signal detection
    - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.3, 6.5_

  
  - [ ] 9.5 Update us30_scanner/main_us30_scalp.py (US30 scalp)
    - Fix YFinance period calculation
    - Increase buffer size to 500
    - Add signal handler for graceful shutdown
    - Add indicator validation before signal detection
    - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.3, 6.5_

  
  - [ ] 9.6 Update us30_scanner/main_us30_swing.py (US30 swing)
    - Fix YFinance period calculation
    - Increase buffer size to 500
    - Add signal handler for graceful shutdown
    - Add indicator validation before signal detection
    - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.3, 6.5_


- [ ] 10. Test and validate fixes
  - [ ] 10.1 Test indicator calculations with edge cases
    - Test with insufficient data (should raise error)
    - Test with missing columns (should raise error)
    - Test with valid data (should return correct values)
    - Verify no NaN values in output

    - _Requirements: 1.1, 1.5, 2.1_
  
  - [ ] 10.2 Test signal detection with historical data
    - Run scanners on historical data with known setups
    - Verify bearish signals detected when price below EMAs
    - Verify bullish signals detected when price above EMAs

    - Check Excel output for proper indicator values
    - _Requirements: 4.2, 4.3, 4.4, 5.4_
  
  - [ ] 10.3 Test WebSocket connections
    - Test Kraken WebSocket connection and subscription
    - Test automatic reconnection after disconnect

    - Verify real-time data updates
    - Check latency and data quality
    - _Requirements: 6.2, 6.3, 6.4_
  
  - [x] 10.4 Test systemd services

    - Test service startup and shutdown
    - Test automatic restart after crash
    - Test graceful shutdown with SIGTERM
    - Monitor resource usage (memory, CPU)
    - _Requirements: 6.1, 6.5, 6.7_
  
  - [x] 10.5 Test Windows batch file launchers

    - Test individual scanner batch files
    - Test start_all_scanners.bat
    - Test stop_all_scanners.bat
    - Verify console windows open correctly
    - _Requirements: N/A (Windows desktop support)_


- [x] 11. Update documentation


  - [ ] 11.1 Update README with new features
    - Document WebSocket support for Kraken
    - Document systemd service deployment
    - Document Windows batch file usage
    - Add troubleshooting section for common issues
    - _Requirements: N/A (Documentation)_

  
  - [ ] 11.2 Create deployment guide
    - Linux systemd deployment instructions
    - Windows desktop deployment instructions
    - Configuration guide for new parameters
    - Monitoring and troubleshooting guide
    - _Requirements: N/A (Documentation)_
