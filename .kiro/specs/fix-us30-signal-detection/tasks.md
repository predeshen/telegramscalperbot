# Implementation Plan

- [x] 1. Add missing indicator calculations to US30 scanner


  - Update main_us30_swing.py to calculate EMA 9, VWAP, and Stochastic indicators
  - Add EMA 9 calculation in both initial data fetch and polling loop
  - Add VWAP calculation in both initial data fetch and polling loop
  - Add Stochastic (K and D) calculation in both initial data fetch and polling loop
  - Verify all indicators are included in Excel logging
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_





- [ ] 2. Implement trend alignment signal detection
  - [ ] 2.1 Create _detect_trend_alignment method in US30SwingDetector
    - Implement bullish cascade detection (Price > EMA9 > EMA21 > EMA50)
    - Implement bearish cascade detection (Price < EMA9 < EMA21 < EMA50)
    - Add RSI validation (> 50 for bullish, < 50 for bearish)

    - Add volume validation (>= 0.8x average)
    - Create signal with proper metadata (strategy, trend_alignment)
    - _Requirements: 2.1, 2.2, 2.5, 3.1, 3.2, 3.5_
  
  - [ ] 2.2 Update detect_signals method to prioritize trend alignment
    - Call _detect_trend_alignment as primary strategy

    - Keep existing _detect_trend_continuation as secondary
    - Keep existing _detect_trend_reversal as tertiary
    - Ensure duplicate checking works for all strategies
    - _Requirements: 2.2, 3.2_
  


  - [ ] 2.3 Implement signal creation for trend alignment
    - Calculate stop loss (entry ± 2.0 * ATR)
    - Calculate take profit (entry ± 3.0 * ATR)
    - Generate detailed reasoning explaining trend alignment
    - Include all indicator values in signal metadata


    - _Requirements: 2.3, 2.4, 3.3, 3.4_

- [ ] 3. Update volume threshold configuration
  - Update config_us30_swing.json volume_spike_threshold from 1.3 to 0.8
  - Add volume_reversal_threshold: 1.2 for trend reversal signals

  - Update _detect_trend_continuation to use 0.8x volume threshold
  - Update _detect_trend_reversal to use 1.2x volume threshold
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 4. Increase scan frequency
  - Remove time-based check interval logic from main scanning loop




  - Allow scanner to check for signals every polling_interval_seconds (300s)
  - Update last_check_times tracking to only prevent duplicate API calls
  - Rely on duplicate detection to filter repeated signals
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_


- [ ] 5. Update duplicate signal prevention
  - Update duplicate_time_window_minutes from 240 to 120 in config
  - Update duplicate_price_threshold_percent from 0.5 to 0.3 in config
  - Verify _is_duplicate method uses updated thresholds
  - Test duplicate detection with new thresholds


  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6. Add diagnostic logging

  - [ ] 6.1 Add scan-level logging
    - Log current price, EMA values, volume ratio, RSI after each scan
    - Log trend alignment status (bullish cascade, bearish cascade, mixed)
    - Log timeframe and timestamp for each scan
    - _Requirements: 7.1, 7.5_
  
  - [x] 6.2 Add signal detection logging


    - Log when trend alignment conditions are met
    - Log when conditions fail with specific reason
    - Log volume ratio and threshold comparison
    - Log RSI level and threshold comparison
    - _Requirements: 7.2, 7.3_
  
  - [ ] 6.3 Add duplicate detection logging
    - Log when duplicate signal is blocked
    - Include previous signal details (price, time)
    - Log time difference and price difference
    - _Requirements: 7.4_

- [ ] 7. Verify Excel reporting includes all indicators
  - Ensure ema_9 is logged to Excel (currently shows NaN)
  - Ensure vwap is logged to Excel (currently shows NaN)
  - Ensure stoch_k is logged to Excel (currently shows NaN)
  - Ensure stoch_d is logged to Excel (currently shows NaN)
  - Test Excel output has no NaN values for calculated indicators
  - _Requirements: 1.4_

- [ ] 8. Update configuration file
  - Update signal_rules.volume_spike_threshold to 0.8
  - Add signal_rules.volume_reversal_threshold: 1.2
  - Update signal_rules.duplicate_time_window_minutes to 120
  - Update signal_rules.duplicate_price_threshold_percent to 0.3
  - Keep polling_interval_seconds at 300
  - _Requirements: 4.1, 4.5, 5.1, 6.1, 6.2_
