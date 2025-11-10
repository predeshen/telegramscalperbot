# Implementation Plan

- [x] 1. Add candle pattern detection helpers to BTC signal detector



  - Create `_is_pin_bar()` method to detect pin bar patterns (long wick, small body)
  - Create `_is_doji()` method to detect doji patterns (very small body)
  - Create `_is_engulfing()` method to detect engulfing candle patterns

  - _Requirements: 6.3_



- [ ] 2. Implement momentum shift detection for BTC
  - [ ] 2.1 Create `_detect_momentum_shift()` method in src/signal_detector.py
    - Check RSI(14) increasing/decreasing over 3 consecutive candles
    - Verify ADX >= 18 for trend strength
    - Confirm volume >= 1.2x average
    - Validate trend context (price vs EMA50)


    - Check recent 10-candle price action aligns with signal direction
    - Generate signal with 2.0 ATR stop loss, 3.0 ATR take profit
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_


  - [ ] 2.2 Add momentum shift to detect_signals() priority order
    - Call `_detect_momentum_shift()` as first strategy check
    - Return signal if found, otherwise continue to next strategy
    - _Requirements: 8.1, 8.3_




  - [ ] 2.3 Add logging for momentum shift detection
    - Log RSI values over last 3 candles
    - Log ADX level and volume ratio
    - Log trend context validation results
    - Log signal generation or rejection reasons
    - _Requirements: 11.1, 11.4_



- [ ] 3. Implement trend alignment detection for BTC
  - [ ] 3.1 Create `_detect_trend_alignment()` method in src/signal_detector.py
    - Check cascade alignment (Price > EMA9 > EMA21 > EMA50 or inverse)

    - Verify RSI > 50 (bullish) or < 50 (bearish)
    - Confirm RSI direction matches signal (rising/falling)
    - Validate ADX >= 19
    - Check volume >= 0.8x average
    - Generate signal with configured ATR multipliers

    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_



  - [ ] 3.2 Add trend alignment to detect_signals() priority order
    - Call `_detect_trend_alignment()` as second strategy check
    - Return signal if found, otherwise continue to next strategy
    - _Requirements: 8.1, 8.3_

  - [x] 3.3 Add logging for trend alignment detection


    - Log EMA cascade status (all EMA values)
    - Log RSI level and direction
    - Log ADX and volume ratio

    - Log specific failure reasons when conditions not met
    - _Requirements: 11.2, 11.4_

- [x] 4. Implement EMA cloud breakout detection for BTC

  - [x] 4.1 Create `_detect_ema_cloud_breakout()` method in src/signal_detector.py


    - Check EMA(21) and EMA(50) alignment
    - Verify price vs VWAP position
    - Confirm RSI in range 25-75
    - Check volume >= 1.5x average
    - Detect range breakout (10-candle high/low)
    - Generate signal with 1.2 ATR stop loss, 1.5 ATR take profit


    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 4.2 Add EMA cloud breakout to detect_signals() priority order

    - Call `_detect_ema_cloud_breakout()` as third strategy check
    - Return signal if found, otherwise continue to next strategy
    - _Requirements: 8.1, 8.3_


  - [x] 4.3 Add logging for EMA cloud breakout detection


    - Log EMA alignment status
    - Log VWAP position and RSI level
    - Log breakout detection (recent high/low comparison)
    - _Requirements: 11.1, 11.4_

- [ ] 5. Implement mean reversion detection for BTC
  - [ ] 5.1 Create `_detect_mean_reversion()` method in src/signal_detector.py
    - Check price overextension (> 1.5 ATR from VWAP)
    - Verify RSI extremes (< 25 or > 75)
    - Detect reversal candle patterns using helper methods

    - Confirm volume >= 1.3x average
    - Generate signal targeting VWAP with 1.0 ATR stop loss
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_



  - [ ] 5.2 Add mean reversion to detect_signals() priority order
    - Call `_detect_mean_reversion()` as fourth strategy check
    - Return signal if found, otherwise continue to existing strategies
    - _Requirements: 8.1, 8.3_

  - [ ] 5.3 Add logging for mean reversion detection
    - Log price distance from VWAP

    - Log RSI extreme level
    - Log reversal pattern detection results
    - _Requirements: 11.1, 11.4_


- [ ] 6. Update BTC configuration
  - [ ] 6.1 Add new signal rule parameters to config/config.json
    - Add `volume_momentum_shift: 1.2`
    - Add `volume_trend_alignment: 0.8`
    - Add `volume_ema_cloud_breakout: 1.5`
    - Add `volume_mean_reversion: 1.3`

    - Add `rsi_momentum_threshold: 3.0`
    - Add `adx_min_momentum_shift: 18`
    - Add `adx_min_trend_alignment: 19`
    - Add `momentum_shift_sl_multiplier: 2.0`
    - Add `momentum_shift_tp_multiplier: 3.0`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 10.1, 10.3_

  - [ ] 6.2 Update SignalDetector __init__ to accept new config parameters
    - Add parameters with defaults for backward compatibility
    - Store config values as instance variables
    - _Requirements: 10.3, 10.4_

- [ ] 7. Enhance US30 momentum shift detection
  - [ ] 7.1 Update `_detect_momentum_shift()` in us30_scanner/us30_swing_detector.py
    - Use RSI(14) instead of RSI(7) for more stable signals
    - Increase ADX threshold to 22
    - Add RSI momentum threshold check (3.0 points minimum)
    - Add optional price confirmation (break above/below previous high/low)
    - Improve logging for debugging
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 7.2 Ensure momentum shift is first in US30 detect_signals() priority
    - Verify momentum shift is called before trend alignment
    - _Requirements: 8.2, 8.3_

- [ ] 8. Enhance US30 trend alignment detection
  - [ ] 8.1 Update `_detect_trend_alignment()` in us30_scanner/us30_swing_detector.py
    - Add comprehensive logging of EMA cascade status
    - Add RSI direction check (rising for bullish, falling for bearish)
    - Log specific failure reasons when conditions not met
    - Use ADX >= 19 threshold
    - Use volume >= 0.8x threshold
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 8.2 Ensure trend alignment is second in US30 detect_signals() priority
    - Verify trend alignment is called after momentum shift, before other strategies
    - _Requirements: 8.2, 8.3_

- [x] 9. Add candle pattern detection helpers to US30 swing detector


  - Create `_is_pin_bar()` method (same logic as BTC)
  - Create `_is_doji()` method (same logic as BTC)
  - Create `_is_engulfing()` method (same logic as BTC)
  - _Requirements: 7.3_

- [x] 10. Implement EMA cloud breakout detection for US30

  - [x] 10.1 Create `_detect_ema_cloud_breakout()` method in us30_scanner/us30_swing_detector.py


    - Check EMA(21) and EMA(50) alignment
    - Verify price vs VWAP position
    - Confirm RSI in range 25-75
    - Check volume >= 1.5x average
    - Detect range breakout (10-candle high/low)
    - Generate US30SwingSignal with 1.2 ATR stop loss, 1.5 ATR take profit
    - _Requirements: 7.1, 7.4_

  - [x] 10.2 Add EMA cloud breakout to US30 detect_signals() priority order


    - Call after trend alignment, before trend continuation
    - _Requirements: 8.2, 8.3_

- [x] 11. Implement mean reversion detection for US30

  - [x] 11.1 Create `_detect_mean_reversion()` method in us30_scanner/us30_swing_detector.py


    - Check price overextension (> 1.5 ATR from VWAP)
    - Verify RSI extremes (< 25 or > 75)
    - Detect reversal candle patterns using helper methods
    - Confirm volume >= 1.3x average
    - Generate US30SwingSignal targeting VWAP with 1.0 ATR stop loss
    - _Requirements: 7.2, 7.5_

  - [x] 11.2 Add mean reversion to US30 detect_signals() priority order


    - Call after EMA cloud breakout, before trend continuation
    - _Requirements: 8.2, 8.3_

- [x] 12. Update US30 configuration

  - [x] 12.1 Update signal rules in us30_scanner/config_us30_swing.json


    - Update `volume_spike_threshold: 0.8` (if not already)
    - Update `rsi_momentum_threshold: 3.0` (if not already)
    - Update `adx_min_momentum_shift: 22` (if not already)
    - Update `adx_min_trend_alignment: 19` (if not already)
    - Add `volume_ema_cloud_breakout: 1.5`
    - Add `volume_mean_reversion: 1.3`
    - Update `require_price_confirmation: false` (make optional)
    - _Requirements: 9.5, 10.2, 10.3_

  - [x] 12.2 Update US30SwingDetector __init__ to use new config parameters

    - Read new volume thresholds from config
    - Store as instance variables for use in detection methods
    - _Requirements: 10.3_

- [x] 13. Add comprehensive error handling

  - [x] 13.1 Add missing indicator checks to all new detection methods

    - Check for required indicators before accessing
    - Return None with debug log if indicators missing
    - _Requirements: 13.1_

  - [x] 13.2 Add NaN value checks to all new detection methods

    - Check for NaN in critical indicators (EMAs, RSI, ADX)
    - Return None with warning log if NaN detected
    - _Requirements: 13.1_

  - [x] 13.3 Add exception handling to all new detection methods

    - Wrap detection logic in try-except blocks
    - Log errors with stack traces
    - Return None on exceptions
    - _Requirements: 13.1_

- [x] 14. Verify existing strategies remain functional

  - [x] 14.1 Verify BTC confluence detection still works

    - Ensure `_check_bullish_confluence()` and `_check_bearish_confluence()` unchanged
    - Verify they are called in correct priority order
    - _Requirements: 12.1, 12.4_

  - [x] 14.2 Verify BTC trend following still works

    - Ensure `_detect_trend_following()` unchanged
    - Verify it is called in correct priority order
    - _Requirements: 12.2, 12.4_

  - [x] 14.3 Verify US30 trend continuation and reversal still work

    - Ensure `_detect_trend_continuation()` and `_detect_trend_reversal()` unchanged
    - Verify they are called in correct priority order
    - _Requirements: 12.3, 12.4_

  - [x] 14.4 Verify H4 HVG detection still works for all assets

    - Ensure H4 HVG is called on 4h timeframe
    - Verify it works for BTC, US30, and Gold
    - _Requirements: 12.4_

- [x] 15. Test BTC signal detection with live data

  - [x] 15.1 Run BTC scanner with live data for 1 hour

    - Monitor for momentum shift signals
    - Monitor for trend alignment signals
    - Monitor for EMA cloud breakout signals
    - Monitor for mean reversion signals
    - Verify signals are generated when conditions met
    - _Requirements: 1.1, 3.1, 5.1, 6.1_

  - [x] 15.2 Verify BTC signal quality

    - Check that signals have valid entry, stop loss, take profit
    - Verify risk/reward ratios are reasonable
    - Confirm duplicate detection works
    - _Requirements: 13.1, 13.5_

  - [x] 15.3 Review BTC signal logs

    - Verify comprehensive logging is working
    - Check that rejection reasons are logged
    - Confirm strategy priority order is correct
    - _Requirements: 11.1, 11.4, 11.5_

- [x] 16. Test US30 signal detection with live data

  - [x] 16.1 Run US30 scanner with live data for 1 hour

    - Monitor for momentum shift signals
    - Monitor for trend alignment signals
    - Monitor for EMA cloud breakout signals
    - Monitor for mean reversion signals
    - Verify signals are generated when conditions met
    - _Requirements: 2.1, 4.1, 7.1, 7.2_

  - [x] 16.2 Verify US30 signal quality

    - Check that signals have valid entry, stop loss, take profit
    - Verify risk/reward ratios are reasonable
    - Confirm duplicate detection works
    - _Requirements: 13.1, 13.5_

  - [x] 16.3 Review US30 signal logs

    - Verify comprehensive logging is working
    - Check that rejection reasons are logged
    - Confirm strategy priority order is correct
    - _Requirements: 11.3, 11.4, 11.5_

- [x] 17. Update documentation


  - [x] 17.1 Update README.md with new strategies

    - Document momentum shift strategy
    - Document trend alignment strategy
    - Document EMA cloud breakout strategy
    - Document mean reversion strategy
    - Explain strategy priority order

  - [x] 17.2 Update configuration documentation

    - Document new config parameters
    - Explain volume thresholds per strategy
    - Explain ADX thresholds
    - Explain RSI momentum threshold
