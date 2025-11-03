# Implementation Plan

- [x] 1. Create TrendAnalyzer helper class


  - Create new file `src/trend_analyzer.py` with swing point detection logic
  - Implement `detect_swing_points()` method to identify swing highs and lows
  - Implement `is_uptrend()` and `is_downtrend()` methods with configurable minimum swing points
  - Implement `calculate_pullback_depth()` to measure retracement percentage
  - Implement `is_ema_aligned()` to verify EMA trend alignment
  - Add comprehensive docstrings and type hints
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_






- [ ] 2. Add trend-following detection to BTC/US30 SignalDetector
- [ ] 2.1 Implement _detect_trend_following method
  - Add `_detect_trend_following()` method to `src/signal_detector.py`
  - Use TrendAnalyzer to detect swing points and identify trends
  - Check for pullback to EMA(21) with bounce confirmation
  - Validate volume (>1.2x average) and RSI range (40-80 for longs, 20-60 for shorts)

  - Calculate stop-loss (1.5x ATR) and take-profit (2.5-3x ATR based on trend strength)
  - Generate Signal with strategy="Trend Following" and trend metadata
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4_

- [ ] 2.2 Integrate trend-following into detect_signals
  - Modify `detect_signals()` method to check for trend-following signals

  - Add trend-following check after existing strategy checks
  - Ensure duplicate detection works with trend-following signals
  - Add logging for trend-following signal generation
  - _Requirements: 4.2, 4.3, 4.6, 4.8, 5.5_





- [ ] 2.3 Add signal quality filters
  - Implement minimum swing point check (reject if < 3 swings)
  - Implement ATR consolidation check (skip if ATR declining 3+ periods)
  - Implement pullback depth check (reject if > 61.8% retracement)


  - Implement volume trend check (reduce confidence if volume declining)
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 3. Add trend-following to XAUUSD GoldSignalDetector
- [ ] 3.1 Add TREND_FOLLOWING to GoldStrategy enum
  - Modify `xauusd_scanner/strategy_selector.py` to add TREND_FOLLOWING enum value
  - Update StrategySelector.select_strategy() to detect and select TREND_FOLLOWING
  - Prioritize TREND_FOLLOWING during strong trending markets

  - Add session-aware logic (prefer London/NY sessions for trend-following)
  - _Requirements: 4.1, 4.4, 4.5_

- [x] 3.2 Implement _detect_trend_following for Gold




  - Add `_detect_trend_following()` method to `xauusd_scanner/gold_signal_detector.py`
  - Use TrendAnalyzer for swing point detection
  - Integrate session awareness (check current session)
  - Integrate key level tracking (check proximity to support/resistance)
  - Add spread monitoring (skip if spread too wide)
  - Include Asian range context in signal reasoning
  - Generate GoldSignal with complete metadata

  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3.3 Update signal routing in detect_signals
  - Modify `detect_signals()` to route to _detect_trend_following when strategy selected
  - Ensure proper signal metadata (strategy, session, Asian range, key levels)
  - Add trend-specific reasoning generation
  - _Requirements: 4.5, 4.7, 4.8, 6.1, 6.2, 6.3, 6.4, 6.5_


- [ ] 4. Enhance ExcelReporter for complete data logging
- [ ] 4.1 Expand Excel column structure
  - Modify `src/excel_reporter.py` to define complete column list
  - Add indicator columns: EMA_9, EMA_21, EMA_50, EMA_100, EMA_200, RSI, ATR, VWAP, Volume_MA
  - Add signal columns: Signal_Detected, Signal_Type, Entry_Price, Stop_Loss, Take_Profit, Risk_Reward


  - Add strategy columns: Strategy, Confidence, Market_Bias, Reasoning
  - Add XAUUSD columns: Session, Spread_Pips, Asian_Range_High, Asian_Range_Low
  - Add trend columns: Trend_Direction, Swing_Points, Pullback_Depth
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_





- [ ] 4.2 Implement complete data extraction
  - Modify `log_scan_result()` to extract all indicator values from scan_data
  - Extract all signal details from signal_details dictionary
  - Extract XAUUSD-specific data (session, spread, Asian range) when present


  - Extract trend-specific data (direction, swing points, pullback) when present
  - Handle nested dictionaries by flattening to individual columns
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 4.3 Implement data formatting and validation


  - Format numeric values (2 decimals for prices, 1 for percentages)
  - Handle missing values (write "N/A" or None appropriately)
  - Validate data types before writing
  - Add error handling for malformed data
  - _Requirements: 8.7, 8.8_


- [x] 4.4 Update email report generation

  - Modify email report to include summary statistics
  - Add total scans count, signals detected count, signal type breakdown
  - Include trend-following signal count in summary
  - Format email body with clear sections
  - _Requirements: 7.8_


- [ ] 5. Update scanner main files to pass complete data
- [ ] 5.1 Update BTC scanner (main_swing.py)
  - Modify scan_data dictionary to include all indicator values

  - Add trend metadata to signal_details when trend-following signal detected
  - Ensure all EMA values (9, 21, 50, 100, 200) are included
  - Pass complete data to excel_reporter.log_scan_result()

  - _Requirements: 7.1, 7.2, 7.3, 7.6_


- [ ] 5.2 Update US30 scanner (us30_scanner/main_us30.py)
  - Modify scan_data dictionary to include all indicator values
  - Add trend metadata to signal_details when trend-following signal detected
  - Ensure all EMA values are included
  - Pass complete data to excel_reporter.log_scan_result()

  - _Requirements: 7.1, 7.2, 7.3, 7.6_

- [ ] 5.3 Update XAUUSD scanner (xauusd_scanner/main_gold_swing.py)
  - Modify scan_data dictionary to include all indicator values
  - Add session information from session_manager
  - Add spread data from spread_monitor

  - Add Asian range data when available
  - Add trend metadata to signal_details when trend-following signal detected
  - Pass complete data to excel_reporter.log_scan_result()
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ] 6. Add configuration for trend-following
- [x] 6.1 Update BTC config (config/config_multitime.json)

  - Add `trend_following` section under `signal_detection`
  - Set enabled=true, min_swing_points=3, max_pullback_percent=50
  - Set min_volume_ratio=1.2, rsi_range_uptrend=[40,80], rsi_range_downtrend=[20,60]
  - _Requirements: 4.2, 4.6_

- [x] 6.2 Update US30 config (us30_scanner/config_us30.json)


  - Add `trend_following` section under `signal_detection`

  - Use same parameters as BTC config
  - _Requirements: 4.3, 4.6_

- [ ] 6.3 Update XAUUSD config (xauusd_scanner/config_gold_swing.json)
  - Add `trend_following` section under `signal_rules`
  - Use same parameters as BTC config

  - _Requirements: 4.1, 4.5, 4.7_

- [ ] 7. Testing and validation
- [ ] 7.1 Test TrendAnalyzer with sample data
  - Create test data with known uptrend pattern
  - Verify swing point detection accuracy
  - Verify uptrend/downtrend identification
  - Test edge cases (insufficient data, flat market)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] 7.2 Test trend-following signal generation
  - Test with historical trending data for each scanner
  - Verify signals generated at appropriate entry points
  - Verify stop-loss and take-profit calculations
  - Verify signal quality filters work correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7.3 Test Excel data logging
  - Run each scanner and verify Excel file created
  - Verify all columns present in Excel file
  - Verify data formatting correct (decimals, N/A for missing)
  - Verify trend-following signals logged with complete metadata
  - Open Excel files manually to inspect data quality
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [ ] 7.4 Integration test with live data
  - Run all three scanners simultaneously for 1 hour
  - Verify no conflicts or errors
  - Verify each scanner logs to correct Excel file
  - Verify email reports sent successfully
  - Check logs for any errors or warnings
  - _Requirements: All requirements_

- [ ] 8. Documentation and deployment
- [ ] 8.1 Update README with trend-following feature
  - Document new trend-following strategy
  - Explain configuration options
  - Provide examples of trend signals
  - Update Excel file structure documentation
  - _Requirements: All requirements_

- [ ] 8.2 Create deployment checklist
  - List all modified files
  - List configuration changes needed
  - List testing steps before production deployment
  - Document rollback procedure
  - _Requirements: All requirements_
