# Implementation Plan

- [x] 1. Create AssetConfigManager for symbol configuration management


  - Create `src/asset_config_manager.py` with configuration loading, validation, and hot-reload functionality
  - Implement symbol categorization by asset type (crypto, fx, commodity)
  - Add configuration validation with detailed error reporting
  - Create default configuration template with BTC, ETH, SOL, AVAX, MATIC, LINK, and major FX pairs
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_


- [x] 2. Create SignalFilter for timeframe conflict resolution and duplicate prevention

  - Create `src/signal_filter.py` with timeframe hierarchy implementation
  - Implement conflict detection logic that compares signal directions across timeframes
  - Add active trade conflict checking to prevent opposite signals
  - Implement FX trading session validation
  - Add signal history tracking with configurable retention
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.2_


- [x] 3. Enhance TradeTracker with grace period and strict exit rules


  - Modify `src/trade_tracker.py` to add grace period enforcement (30 minutes)
  - Implement profit threshold validation (no exits on negative P&L)
  - Add peak profit tracking and giveback percentage calculation
  - Implement duplicate exit signal prevention (10-minute window)
  - Add per-symbol trade tracking with separate trade dictionaries
  - Update exit signal logic to check: grace period, profit thresholds, giveback limits
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 4. Create SymbolScanner for individual symbol scanning



  - Create `src/symbol_scanner.py` that wraps existing scanner components
  - Initialize YFinanceClient, IndicatorCalculator, and SignalDetector per symbol
  - Implement scan_timeframe method that fetches data, calculates indicators, and detects signals
  - Add asset-specific parameter application from configuration
  - Implement signal callback mechanism to report signals to orchestrator
  - Add error handling for connection failures and data issues
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Create SymbolOrchestrator for multi-symbol coordination



  - Create `src/symbol_orchestrator.py` that manages multiple SymbolScanner instances
  - Implement add_symbol and remove_symbol methods for dynamic symbol management
  - Add parallel scanning using threading (one thread per symbol)
  - Implement signal coordination that filters signals through SignalFilter before alerting
  - Add graceful startup with staggered symbol initialization (1-second delay between symbols)
  - Implement graceful shutdown that stops all scanners and waits for threads
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Enhance alerter with symbol-specific formatting


  - Modify `src/alerter.py` to include symbol emoji and display name in alerts
  - Add asset type indicator (crypto/fx) to alert messages
  - Include 24h change percentage in alerts
  - Add scanner type (scalp/swing) to alert titles
  - Update alert formatting to clearly distinguish between symbols
  - _Requirements: 6.1, 6.2, 6.4, 6.5_


- [x] 7. Create multi-symbol configuration files

  - Create `config/multi_crypto_scalp.json` with BTC, ETH, SOL for 1m/5m/15m timeframes
  - Create `config/multi_crypto_swing.json` with BTC, ETH for 15m/1h/4h/1d timeframes
  - Create `config/multi_fx_scalp.json` with EUR/USD, GBP/USD, USD/JPY for 5m/15m/1h timeframes
  - Create `config/multi_mixed.json` with both crypto and FX symbols
  - Include asset-specific parameters for each symbol (volume thresholds, RSI ranges, ATR multipliers)
  - Add exit rules configuration (grace period, profit thresholds, giveback limits)
  - _Requirements: 1.5, 3.1, 3.2, 3.3, 4.2, 4.3, 7.1, 7.2, 7.3, 8.2, 8.3, 13.5_


- [x] 8. Create main entry point for multi-symbol scanner

  - Create `main_multi_symbol.py` that initializes SymbolOrchestrator
  - Load configuration from specified config file (command-line argument)
  - Initialize AssetConfigManager and load symbol configurations
  - Create and start SymbolOrchestrator with loaded configurations
  - Add signal handlers for graceful shutdown (SIGINT, SIGTERM)
  - Implement heartbeat messages that include status of all active symbols
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.4_

- [x] 9. Create Windows batch files for easy scanner startup



  - Create `start_multi_crypto_scalp.bat` that runs main_multi_symbol.py with crypto scalp config
  - Create `start_multi_crypto_swing.bat` that runs main_multi_symbol.py with crypto swing config
  - Create `start_multi_fx_scalp.bat` that runs main_multi_symbol.py with FX scalp config
  - Create `start_multi_mixed.bat` that runs main_multi_symbol.py with mixed config
  - Add environment checks and virtual environment activation
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 10. Add volatility and volume monitoring


  - Add volatility calculation (24h ATR percentage) to SymbolScanner
  - Add average volume calculation to SymbolScanner
  - Implement dynamic signal sensitivity adjustment based on volatility
  - Add volume-based pause logic (pause when volume below threshold)
  - Include volatility and volume metrics in Excel reporting
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 11. Implement FX trading session detection

  - Create `src/trading_session.py` with session time detection logic
  - Implement session identification (Asian, London, NewYork, overlaps)
  - Add session-based confidence score adjustment for FX pairs
  - Implement primary session requirement enforcement
  - Add session information to FX signal alerts
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_


- [x] 12. Update Excel reporter for multi-symbol support


  - Modify `src/excel_reporter.py` to include asset_type column (crypto/fx/commodity/index)
  - Add scanner_type column (scalp/swing) to headers
  - Include volatility metrics (24h ATR percentage) in reports
  - Include volume metrics (average volume, volume spike ratio) in reports
  - Create separate sheets per symbol in Excel workbook for better organization
  - Update log_scan_result method to accept and log asset_type and scanner_type
  - _Requirements: 1.5, 6.2, 6.3_


- [x] 13. Add configuration validation and error handling


  - Add symbol availability check with Yahoo Finance on startup in AssetConfigManager
  - Implement per-symbol error tracking in SymbolScanner (count consecutive errors)
  - Add automatic pause logic when error rate exceeds threshold (e.g., 5 consecutive errors)
  - Implement admin alerts for disabled symbols via Telegram
  - Add reconnection logic with exponential backoff in SymbolScanner for failed symbols
  - Create error_tracker dictionary in SymbolOrchestrator to monitor symbol health
  - _Requirements: 2.1, 13.3, 13.4_

- [x] 14. Implement signal quality improvements


  - Add candle confirmation period in SignalDetector (wait for candle close + 1 additional candle)
  - Implement conflicting signal suppression in SignalFilter for signals within 15 minutes
  - Add ADX-based confluence requirement adjustment (increase min_confluence when ADX < 20)
  - Implement per-symbol win rate tracking in TradeTracker
  - Add dynamic sensitivity adjustment based on recent win rate (reduce min_confidence if win rate > 60%)
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ] 15. Create comprehensive logging and monitoring



  - Add per-symbol log files with rotation in SymbolScanner (e.g., logs/btc_scanner.log)
  - Implement suppressed signal logging with reasons in SignalFilter
  - Add performance metrics logging (scan duration, signal count per symbol) in SymbolOrchestrator
  - Create summary statistics in logs (signals per hour, win rate, avg confidence)
  - Add health check status file (e.g., logs/scanner_health.json) with symbol status
  - _Requirements: 4.4, 10.5_


- [x] 16. Create FVGDetector for Fair Value Gap detection

  - Create `src/fvg_detector.py` with FVGZone dataclass
  - Implement detect_fvgs method that identifies gaps where candle[i-1] doesn't overlap candle[i+1]
  - Add inverse FVG detection (bearish): candle[i-1].low > candle[i+1].high
  - Add regular FVG detection (bullish): candle[i-1].high < candle[i+1].low
  - Implement minimum gap percentage filter (default 0.2%)
  - Add FVG zone tracking with filled/unfilled status
  - _Requirements: 13.1, 13.2, 13.4_

- [x] 17. Implement lower timeframe confirmation for FVG signals


  - Add check_fvg_reentry method to detect when price returns to FVG zone
  - Implement detect_lower_tf_shift to identify market structure breaks within FVG zones
  - For inverse FVG: detect break of structure (BOS) to downside with lower high
  - For regular FVG: detect break of structure (BOS) to upside with higher low
  - Add confirmation logic that requires both FVG re-entry AND lower TF shift
  - _Requirements: 14.1, 14.2_


- [x] 18. Add FVG target calculation and signal generation
  - Implement calculate_fvg_targets to find swing lows/highs for target levels
  - Identify liquidity pools (previous swing points with multiple touches)
  - Generate FVG signals with zone boundaries, entry, stop-loss, and targets
  - Add FVG zone information to signal alerts (high/low boundaries)
  - Implement FVG zone "filled" tracking when price fully retraces
  - _Requirements: 14.2, 14.3, 14.4_


- [x] 19. Integrate FVG detection into SymbolScanner
  - Add FVGDetector instance to SymbolScanner
  - Scan higher timeframes (4h, 1d) for FVG zones on each update
  - Monitor lower timeframes (15m, 1h) for confirmation when price in FVG zone
  - Prioritize FVG signals over standard EMA crossover signals
  - Add FVG strategy to signal reasoning and alert messages
  - _Requirements: 13.3, 13.5, 14.5_

- [x] 20. Create NWOGDetector for New Week Opening Gap detection



  - Create `src/nwog_detector.py` with NWOGZone dataclass
  - Implement detect_nwog method that identifies gaps between Friday close and Monday open
  - Add minimum gap percentage filter (default 0.1%)
  - Implement check_nwog_respect to detect price rejection at NWOG zones

  - Add target calculation based on previous week's swing points
  - Track NWOG zones with respect count (how many times price respected the level)
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 21. Create DivergenceAnalyzer for inter-market divergence detection
  - Create `src/divergence_analyzer.py` with DivergenceSignal dataclass
  - Implement price data tracking for multiple correlated symbols (US30, SPX, NDX)
  - Add detect_divergence method that compares new highs/lows across indices
  - Implement divergence strength calculation (0-100 scale)
  - Add bullish divergence detection (primary makes new low, references don't)
  - Add bearish divergence detection (primary makes new high, references don't)
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 22. Integrate NWOG detection into SymbolScanner
  - Add NWOGDetector instance to SymbolScanner for index symbols (US30, SPX, NDX)
  - Scan for NWOG zones on weekly/daily timeframes
  - Monitor for NWOG respect on lower timeframes (4h, 1h)
  - Increase signal confidence when NWOG aligns es
  - Monitor for NWOG respect on lower timeframes (4h, 1h)
  - Feed price data to DivergenceAnalyzer for all index symbols
  - Check for divergence when generating signals for indices

  - Increase signal confidence when divergence aligns with NWOG or FVG zones
  - _Requirements: 15.4, 16.4_

- [x] 23. Enhance signal alerts with NWOG and divergence information

  - Add NWOG zone boundaries to signal alerts when NWOG is the trigger
  - Include divergence information in alerts (which indices are diverging)
  - Add divergence strength indicator to signal confidence calculation
  - Update alert formatting to show NWOG respect count
  - Include inter-market context in reasoning section of alerts
  - _Requirements: 15.5, 16.5_

- [x] 24. Create documentation and configuration guide


  - Create `docs/MULTI_SYMBOL_SETUP.md` with setup instructions
  - Document configuration file structure and all available parameters
  - Provide recommended settings for different trading styles (scalp vs swing)
  - Add FVG detection configuration and examples
  - Add NWOG detection configuration for indices
  - Add divergence analysis setup for correlated symbols

  - Add troubleshooting guide for common issues
  - Create migration guide from single-symbol to multi-symbol scanner
  - _Requirements: 17.5_


- [x] 25. Create integration tests for multi-symbol scanning





  - Write test for parallel symbol scanning without blocking
  - Write test for timeframe conflict resolution (LONG 15m + SHORT 1d scenario)
  - Write test for premature exit signal prevention
  - Write test for grace period enforcement
  - Write test for FX session validation
  - Write test for configuration hot-reload

  - Write test for FVG detection on sample data
  - Write test for lower timeframe confirmation logic
  - Write test for NWOG detection with Friday-Monday gap data
  - Write test for divergence detection with correlated indices
  - _Requirements: All_

- [x] 26. Perform end-to-end testing with live data

  - Test multi-crypto scalp scanner with BTC, ETH, SOL
  - Test multi-crypto swing scanner with BTC, ETH
  - Test multi-FX scalp scanner with EUR/USD, GBP/USD
  - Test mixed scanner with crypto and FX symbols
  - Test FVG detection on Nasdaq with daily inverse FVG scenario
  - Test NWOG detection on US30 with previous week's gap
  - Test divergence detection between US30, SPX, and NDX
  - Validate exit signal improvements (no premature exits)
  - Validate conflict resolution (no simultaneous LONG/SHORT)
  - Validate FVG signals with lower timeframe confirmation
  - Validate NWOG respect signals with rejection patterns
  - Validate divergence-enhanced signal confidence
  - _Requirements: All_
