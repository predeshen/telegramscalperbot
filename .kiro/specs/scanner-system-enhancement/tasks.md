# Scanner System Enhancement - Implementation Plan

## Phase 1: Foundation and Data Source Unification

- [x] 1. Create unified data source abstraction layer


  - Implement `UnifiedDataClient` class with automatic fallback logic
  - Add data freshness validation (5-minute threshold)
  - Implement retry logic with exponential backoff (1s, 2s, 4s, 8s)
  - Add data source priority: Binance > Twelve Data > Alpha Vantage > MT5
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 11.1, 11.2, 11.3, 11.4, 11.5_


- [x] 2. Enhance configuration system for unified architecture

  - Extend `ConfigLoader` to support symbol-specific overrides
  - Add configuration validation with clear error messages
  - Implement asset-specific parameter loading (BTC, XAUUSD, US30, US100)
  - Add strategy configuration loading
  - _Requirements: 1.1, 1.2, 1.3, 12.1, 12.2, 12.3, 12.4, 12.5_


- [x] 3. Implement indicator calculation enhancements

  - Add Fibonacci retracement level calculation (23.6%, 38.2%, 50%, 61.8%, 78.6%)
  - Add swing point identification (highs/lows over lookback period)
  - Add support/resistance level identification with tolerance grouping
  - Optimize indicator calculations for performance
  - _Requirements: 3.1, 3.2, 5.1, 5.2_

## Phase 2: Strategy Detection Engine


- [x] 4. Create pluggable strategy detection framework

  - Implement `StrategyDetector` base class with strategy registry
  - Add strategy priority logic based on market conditions (volatility, trend, range)
  - Implement strategy coordination and signal selection
  - Add strategy metadata tracking for signal details
  - _Requirements: 1.1, 1.2, 10.1, 10.2, 10.3_


- [x] 5. Implement Fibonacci Retracement strategy

  - Detect swing highs and lows over configurable lookback (default 50 candles)
  - Calculate Fibonacci levels from swing points
  - Monitor for price approach to Fibonacci levels (0.5% tolerance)
  - Detect reversal patterns (pin bar, engulfing, doji) at Fibonacci levels
  - Generate signals with confidence 4/5 when pattern detected
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_



- [x] 6. Implement H4 HVG (Higher Volume Gap) strategy

  - Analyze 4-hour timeframe for gaps exceeding 0.15% of price
  - Detect volume spikes (1.5x average) on gap candles
  - Track gaps and identify gap fill targets
  - Generate signals when price approaches gap fill on lower timeframes
  - Calculate SL at 1.5x ATR and validate minimum 1.5:1 risk/reward

  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Implement Support/Resistance strategy


  - Identify support/resistance levels based on price touches (minimum 2 touches)
  - Group nearby touches using tolerance (0.3% default)
  - Monitor for price approach to S/R levels
  - Detect reversal patterns at S/R levels
  - Generate signals with confidence 4/5 when pattern detected
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

## Phase 3: Intelligent TP/SL Calculation


- [x] 8. Implement historical price action-based TP/SL calculator

  - Analyze last 100+ candles for reversal points
  - Calculate mode (most common distance) of reversals from entry
  - Use historical mode for SL placement instead of fixed ATR multiples
  - Identify most common profit-taking levels for TP placement
  - Implement fallback to ATR-based calculation (1.2x SL, 2.0x TP) if insufficient data
  - Validate minimum 1.2:1 risk/reward ratio and reject signals below threshold
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

## Phase 4: Signal Quality and Live/Future Detection


- [x] 9. Enhance signal quality filter with confluence validation

  - Implement 7-factor confluence system (trend, volume, RSI, S/R, Fibonacci, H4 HVG, pattern)
  - Require minimum 4 confluence factors for signal acceptance
  - Implement confidence scoring (3/5 for 4 factors, 4/5 for 5 factors, 5/5 for 6+ factors)
  - Add duplicate signal detection with configurable time window
  - Validate risk/reward ratios (minimum 1.2:1)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_


- [x] 10. Implement live and future signal detection


  - Detect live signals on current candle (immediate alert)
  - Predict future signals for next 1-3 candles based on pattern analysis
  - Generate preparatory alerts for future signals with predicted levels
  - Track future signal materialization over 3-candle window
  - Send "Signal Cancelled" notification if future signal doesn't materialize
  - Send updated alert when future signal materializes into live signal
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

## Phase 5: Unified Scanner Architecture

- [x] 11. Create unified scanner base class


  - Implement `BaseScanner` with common initialization and polling logic
  - Add symbol-specific configuration loading
  - Implement data fetching with freshness validation
  - Add indicator calculation pipeline
  - Implement strategy detection coordination
  - Add alert delivery and trade tracking
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_


- [x] 12. Consolidate 8 scanner implementations

  - Create `BTCScalpScanner` extending `BaseScanner` with BTC-specific config
  - Create `BTCSwingScanner` extending `BaseScanner` with BTC swing config
  - Create `GoldScalpScanner` extending `BaseScanner` with XAUUSD scalp config
  - Create `GoldSwingScanner` extending `BaseScanner` with XAUUSD swing config
  - Create `US30ScalpScanner` extending `BaseScanner` with US30 scalp config
  - Create `US30SwingScanner` extending `BaseScanner` with US30 swing config
  - Create `US100Scanner` extending `BaseScanner` with US100 config
  - Create `MultiCryptoScanner` extending `BaseScanner` with multi-symbol config
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_


- [x] 13. Implement scanner orchestrator for unified management

  - Create `ScannerOrchestrator` to manage all 8 scanner instances
  - Implement `start_all_scanners()` method
  - Implement `stop_all_scanners()` method
  - Implement `restart_all_scanners()` method
  - Implement `get_scanner_status()` for individual scanner status
  - Implement `get_all_scanner_status()` for system-wide status
  - Add health monitoring across all scanners
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

## Phase 6: Deployment and Operations


- [x] 14. Create unified deployment scripts

  - Create `fresh_install.sh` for complete system installation on new VMs
  - Create `start_all_scanners.sh` to start all 8 scanners with single command
  - Create `stop_all_scanners.sh` to stop all 8 scanners with single command
  - Create `restart_all_scanners.sh` to restart all 8 scanners with single command
  - Implement error handling and logging in all scripts
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_



- [ ] 15. Create systemd service files for all scanners
  - Create `btc-scalp-scanner.service` with proper dependencies
  - Create `btc-swing-scanner.service` with proper dependencies
  - Create `gold-scalp-scanner.service` with proper dependencies
  - Create `gold-swing-scanner.service` with proper dependencies
  - Create `us30-scalp-scanner.service` with proper dependencies
  - Create `us30-swing-scanner.service` with proper dependencies
  - Create `us100-scanner.service` with proper dependencies
  - Create `multi-crypto-scanner.service` with proper dependencies
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

## Phase 7: Codebase Cleanup




- [ ] 16. Remove unused documentation and shell scripts
  - Delete all unused .md files (keep only README.md and DEPLOYMENT_GUIDE.md)
  - Delete all unused .sh files (keep only deployment scripts from Phase 6)
  - Remove obsolete configuration files
  - Clean up logs directory

  - _Requirements: 9.1, 9.2_



- [ ] 17. Consolidate duplicate code and organize structure
  - Move scanner-specific code to unified `scanners/` directory
  - Consolidate strategy implementations into single modules
  - Remove duplicate utility functions
  - Organize imports and dependencies
  - _Requirements: 9.3, 9.4, 9.5_


## Phase 8: Testing and Validation

- [x] 18. Create comprehensive test suite

  - Write unit tests for Fibonacci retracement calculation
  - Write unit tests for support/resistance identification
  - Write unit tests for historical TP/SL calculation
  - Write unit tests for signal quality filtering
  - Write unit tests for configuration validation

  - _Requirements: 1.1, 3.1, 5.1, 6.1, 12.1_


- [ ] 19. Create integration tests
  - Write end-to-end signal detection flow tests
  - Write data source fallback logic tests
  - Write multi-scanner coordination tests
  - Write alert delivery tests (email, Telegram)


  - Write trade tracking integration tests
  - _Requirements: 1.1, 2.1, 8.1, 11.1_


- [ ] 20. Validate system operation
  - Run 24+ hour system test with all 8 scanners
  - Validate data freshness across all timeframes
  - Test error recovery scenarios (data source failures, network issues)
  - Monitor performance (CPU, memory, network usage)
  - Verify all alerts are delivered correctly
  - _Requirements: 1.1, 2.1, 8.1, 10.1, 11.1_

## Phase 9: Documentation and Handoff

- [x] 21. Create comprehensive documentation



  - Update README.md with new architecture overview
  - Create DEPLOYMENT_GUIDE.md with step-by-step instructions
  - Document configuration options and asset-specific parameters
  - Document strategy selection and priority logic
  - Create troubleshooting guide for common issues
  - _Requirements: 1.1, 8.1, 12.1_

- [x] 22. Create operational runbooks

  - Create scanner startup/shutdown procedures
  - Create data freshness troubleshooting guide
  - Create signal quality troubleshooting guide
  - Create alert delivery troubleshooting guide
  - Create performance monitoring guide
  - _Requirements: 8.1, 11.1, 12.1_



