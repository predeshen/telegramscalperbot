# Implementation Plan

- [x] 1. Create H4 HVG Core Detection Module
  - Create new H4HVGDetector class with gap detection logic
  - Implement gap size calculation (absolute and percentage)
  - Add volume spike validation against moving average
  - Create GapInfo dataclass for gap information storage
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.1 Implement gap detection algorithm
  - Write method to calculate gap between consecutive candles
  - Add gap direction classification (bullish/bearish)
  - Implement gap age tracking (candles since gap occurred)
  - Add minimum gap size filtering
  - _Requirements: 1.1, 1.3, 1.4, 1.5_

- [x] 1.2 Add volume spike validation
  - Implement volume ratio calculation against 20-period MA
  - Add configurable volume spike threshold (default 1.5x)
  - Create volume validation method
  - _Requirements: 1.2_

- [x] 1.3 Create market-specific configurations
  - Define gap thresholds for BTC (0.15%), Gold (0.10%), US30 (0.08%)
  - Add market-specific volume thresholds
  - Implement configuration loading by symbol
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2. Implement Signal Generation Logic
  - Add LONG signal generation for bullish H4 HVG patterns
  - Add SHORT signal generation for bearish H4 HVG patterns
  - Implement entry price calculation at current candle close
  - Create stop-loss calculation using gap levels and ATR
  - Add take-profit calculation using gap size multiplier
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 2.1 Create LONG signal generation
  - Implement bullish gap detection (gap up)
  - Set entry price to current candle close
  - Calculate stop-loss at gap low minus 1.5 ATR
  - Set take-profit at entry plus 2.0x gap size
  - Validate minimum 1.5:1 risk-reward ratio
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2.2 Create SHORT signal generation
  - Implement bearish gap detection (gap down)
  - Set entry price to current candle close
  - Calculate stop-loss at gap high plus 1.5 ATR
  - Set take-profit at entry minus 2.0x gap size
  - Validate minimum 1.5:1 risk-reward ratio
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Add Confluence Validation System
  - Implement EMA trend confirmation (price vs EMA 50)
  - Add RSI range validation (30-70)
  - Create gap recency check (within 3 candles)
  - Implement confidence scoring (3-5 based on factors)
  - Add confluence factor tracking for reasoning
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 3.1 Implement EMA trend confirmation
  - Add bullish bias check (price > EMA 50)
  - Add bearish bias check (price < EMA 50)
  - Integrate EMA confirmation into signal validation
  - _Requirements: 4.1, 4.2_

- [x] 3.2 Add RSI momentum validation
  - Implement RSI range check (30-70)
  - Add RSI validation to signal generation
  - Track RSI as confluence factor
  - _Requirements: 4.3_

- [x] 3.3 Create gap recency validation
  - Implement gap age tracking
  - Add maximum gap age check (3 candles)
  - Filter out stale gaps
  - _Requirements: 4.4_

- [x] 4. Implement Duplicate Signal Prevention
  - Add signal history tracking with timestamps
  - Create duplicate detection based on time and price
  - Implement 4-hour time window for duplicates
  - Add 0.5% price threshold for duplicate filtering
  - Create signal history cleanup (24-hour retention)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4.1 Create signal history management
  - Implement signal storage with timestamp and price
  - Add signal history cleanup for old entries
  - Create efficient duplicate lookup
  - _Requirements: 5.1, 5.5_

- [x] 4.2 Add duplicate detection logic
  - Implement time-based duplicate check (240 minutes)
  - Add price-based duplicate check (0.5% threshold)
  - Create duplicate rejection mechanism
  - _Requirements: 5.2, 5.3, 5.4_

- [x] 5. Enhance Signal Object for H4 HVG
  - Extend Signal dataclass with gap_info field
  - Add volume_spike_ratio field
  - Add confluence_factors list field
  - Update signal creation to include H4 HVG data
  - Set strategy field to "H4 HVG"
  - _Requirements: 6.3, 7.1_

- [x] 5.1 Extend Signal dataclass
  - Add GapInfo field to Signal class
  - Add volume_spike_ratio field
  - Add confluence_factors list field
  - Update Signal constructor
  - _Requirements: 6.3_

- [x] 6. Create Detailed Reasoning System
  - Implement reasoning generation for H4 HVG signals
  - Add gap size description (absolute and percentage)
  - Include volume spike magnitude in reasoning
  - List all confluence factors in explanation
  - Format reasoning with clear sections
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 6.1 Implement reasoning text generation
  - Create structured reasoning format
  - Add gap pattern description
  - Include volume confirmation details
  - List confluence factors
  - Add entry logic explanation
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7. Integrate H4 HVG into Base SignalDetector
  - Add H4HVGDetector instance to SignalDetector
  - Modify detect_signals method to include H4 HVG
  - Add 4-hour timeframe handling
  - Integrate H4 HVG with existing signal flow
  - Update signal priority and selection logic
  - _Requirements: 6.1, 6.2_

- [x] 7.1 Modify SignalDetector class
  - Add H4HVGDetector initialization
  - Update detect_signals method
  - Add 4-hour timeframe check
  - Integrate H4 HVG signal generation
  - _Requirements: 6.1, 6.2_

- [x] 8. Update BTC Scalping Scanner (main.py)
  - Add "4h" to timeframes configuration
  - Update indicator calculation for 4-hour data
  - Integrate H4 HVG detection in main loop
  - Update Excel logging for H4 HVG metrics
  - Test H4 HVG integration with BTC scalping
  - _Requirements: 6.1, 6.5_

- [x] 8.1 Update BTC scalping configuration
  - Add 4-hour timeframe to config
  - Update market data fetching
  - Add H4 HVG configuration section
  - _Requirements: 6.1_

- [x] 8.2 Integrate H4 HVG detection
  - Update main scanning loop
  - Add H4 HVG signal processing
  - Update alert generation
  - _Requirements: 6.2, 6.4_

- [x] 9. Update BTC Swing Scanner (main_swing.py)
  - Add "4h" to timeframes if not present
  - Update indicator calculation for 4-hour data
  - Integrate H4 HVG detection in main loop
  - Update Excel logging for H4 HVG metrics
  - Test H4 HVG integration with BTC swing trading
  - _Requirements: 6.1, 6.5_

- [x] 9.1 Update BTC swing configuration
  - Verify 4-hour timeframe inclusion
  - Add H4 HVG configuration section
  - Update market data handling
  - _Requirements: 6.1_

- [x] 9.2 Integrate H4 HVG detection
  - Update main scanning loop
  - Add H4 HVG signal processing
  - Update alert generation
  - _Requirements: 6.2, 6.4_

- [x] 10. Update Gold Scalping Scanner (xauusd_scanner/main_gold.py)

  - Add H4 HVG detection capability to GoldSignalDetector
  - Integrate H4 HVG detection in main loop
  - Update Excel logging for H4 HVG metrics
  - _Requirements: 6.1, 6.5, 8.2_

- [x] 10.1 Update Gold scanner configuration
  - Add 4-hour timeframe to config
  - Add Gold-specific H4 HVG settings
  - Update market data fetching
  - _Requirements: 6.1, 8.2_

- [x] 10.2 Enhance GoldSignalDetector


  - Add H4 HVG detection capability
  - Integrate with session management
  - Update signal processing
  - _Requirements: 6.2, 6.4_

- [x] 11. Update Gold Swing Scanner (xauusd_scanner/main_gold_swing.py)


  - Add H4 HVG configuration to config file
  - Integrate H4 HVG detection in main loop
  - Update Excel logging
  - _Requirements: 6.1, 6.5, 8.2_


- [ ] 12. Update US30 Scalping Scanner (us30_scanner/main_us30_scalp.py)
  - Add H4 HVG detection capability to US30ScalpDetector
  - Integrate H4 HVG detection in main loop
  - Update Excel logging for H4 HVG metrics
  - _Requirements: 6.1, 6.5, 8.3_

- [x] 12.1 Update US30 scanner configuration
  - Add 4-hour timeframe to config
  - Add US30-specific H4 HVG settings
  - Update market data fetching
  - _Requirements: 6.1, 8.3_

- [x] 12.2 Enhance US30ScalpDetector


  - Add H4 HVG detection capability
  - Integrate with existing strategies
  - Update signal processing
  - _Requirements: 6.2, 6.4_

- [x] 13. Update US30 Swing Scanner (us30_scanner/main_us30_swing.py)


  - Add H4 HVG configuration to config file
  - Integrate H4 HVG detection in main loop
  - Update Excel logging
  - _Requirements: 6.1, 6.5, 8.3_

- [x] 14. Enhance Excel Logging for H4 HVG
  - Add gap_size_percent field to scan data
  - Add volume_spike_ratio field to scan data
  - Update signal_details with H4 HVG metrics
  - Add H4 HVG strategy identification in scanner name
  - Test Excel logging with H4 HVG signals
  - _Requirements: 6.5_

- [x] 14.1 Update Excel data structure
  - Add H4 HVG-specific fields
  - Update scan data dictionary
  - Modify Excel reporter schema
  - _Requirements: 6.5_

- [x] 15. Create Configuration Files for H4 HVG
  - Add H4 HVG section to config/config.json (BTC)
  - Add H4 HVG section to config/config_multitime.json (BTC Swing)
  - Add H4 HVG section to xauusd_scanner/config_gold.json
  - Add H4 HVG section to us30_scanner/config_us30_scalp.json
  - Create market-specific override configurations
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 15.1 Create base H4 HVG configurations
  - Add default H4 HVG settings to all config files
  - Set market-specific thresholds
  - Add configuration validation


  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 16. Update Alert Messages for H4 HVG
  - Enhance alert formatting for H4 HVG signals
  - Include gap size and volume information
  - Add confluence factors to alert text
  - Update Telegram message formatting
  - Test alert generation across all scanners
  - _Requirements: 6.4_



- [ ] 16.1 Create H4 HVG alert templates
  - Design alert message format
  - Include gap and volume details
  - Add confluence information
  - Update alerter classes
  - _Requirements: 6.4_