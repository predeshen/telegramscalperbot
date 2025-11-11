# Implementation Plan

- [x] 1. Create Signal Quality Filter core component



  - Implement SignalQualityFilter class with evaluate_signal method that orchestrates all quality checks
  - Implement calculate_confluence_factors method to evaluate 7 confluence factors (trend, momentum, volume, price action, S/R, MTF, volatility)
  - Implement calculate_confidence_score method with weighted scoring (critical factors 3pts, supporting 2pts, context 1pt) and 1-5 score mapping
  - Implement check_duplicate method with time window checking and price tolerance matching (0.5% threshold)
  - Implement validate_risk_reward method to calculate RR ratio and apply score adjustments
  - Add recent_signals cache with timestamp and price tracking for duplicate detection
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 7.1, 7.2, 7.3, 7.4, 7.5, 14.1, 14.2, 14.3, 14.4, 14.5_



- [ ] 2. Enhance Configuration Manager with asset-specific thresholds
  - Create configuration structure with asset-specific sections for BTC/USD, XAU/USD, and US30
  - Add min_confluence_factors and min_confidence_score per asset (default 4 for both)
  - Add ADX thresholds per asset (BTC: 20, XAU: 19, US30: 22)
  - Add volume_thresholds per strategy per asset (momentum_shift: 1.2x for XAU/BTC, 0.8x for US30; trend_alignment: 0.8x; breakout: 1.5x; mean_reversion: 1.5x)
  - Add rsi_momentum_threshold per asset (3.0 for BTC/US30, 2.5 for XAU)
  - Add trading_hours configuration per asset for liquidity filtering
  - Add duplicate_window_minutes per timeframe type (scalp: 5min, swing: 60min)


  - Implement configuration validation on load with sensible defaults
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.5, 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 3. Enhance Momentum Shift Strategy with trend validation and stricter thresholds
  - Add _validate_trend_alignment method to check price vs EMA50 (LONG: price > EMA50, SHORT: price < EMA50)
  - Implement RSI momentum threshold check (3.0 points for BTC/US30, 2.5 for XAU over 2 candles)
  - Add _confirm_price_action method to verify last 10 candles align with signal direction


  - Update volume requirement logic to use asset-specific thresholds from config (1.2x for XAU/BTC, 0.8x for US30)
  - Add rejection logging with specific reasons (trend conflict, insufficient RSI momentum, price action mismatch, low volume)
  - Update detect_signal method to call all new validation methods before generating preliminary signal
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4_

- [x] 4. Enhance Trend Alignment Strategy with stricter ADX requirements

  - Update ADX threshold check to use asset-specific values from config (BTC: 20, XAU: 19, US30: 22)

  - Add ADX value to signal metadata for trader reference
  - Add rejection logging when ADX is below threshold with actual ADX value
  - Verify volume requirement remains at 0.8x average for all assets
  - Add EMA cascade strength validation to ensure clear trend structure
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.4_


- [-] 5. Enhance EMA Cloud Breakout Strategy with stricter breakout confirmation

  - Implement breakout validation requiring price to break recent 10-candle high/low by at least 0.2%
  - Update volume requirement to 1.5x average for breakout confirmation
  - Add RSI range filter to require RSI between 30 and 70 (avoid extremes)
  - Update stop-loss calculation to use tighter 1.2 ATR (from default)
  - Update take-profit calculation to use conservative 1.5 ATR (from default)
  - Add rejection logging for weak volume or insufficient breakout distance

  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 6. Enhance Mean Reversion Strategy with stricter reversal requirements
  - Update VWAP distance requirement to 1.8 ATR (from 1.5 ATR)
  - Update RSI extreme thresholds to <20 for oversold and >80 for overbought (from 25/75)
  - Implement reversal pattern detection for pin bar, engulfing, and doji formations
  - Update volume requirement to 1.5x average (from 1.3x)
  - Add rejection logging with specific failure reasons (insufficient VWAP distance, RSI not extreme, weak pattern, low volume)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 7. Enhance H4 HVG Strategy with gap quality validation

  - Implement gap size validation requiring minimum 0.3% of price
  - Add volume spike detection requiring 2.0x average at gap formation
  - Implement momentum confirmation when price approaches gap (RSI confirming direction)
  - Integrate with Signal Quality Filter to apply same confluence requirements (min 4 factors)
  - Add rejection logging for small gaps or insufficient volume with gap metrics
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_


- [x] 8. Implement comprehensive diagnostic logging system

  - Add DEBUG level logging for strategy evaluation with indicator values and condition checks
  - Add INFO level logging for signal generation with full signal details and market context
  - Add INFO level logging for signal rejection with specific reasons and threshold values
  - Add INFO level logging for confluence factor evaluation results (which passed/failed)
  - Add INFO level logging for confidence score calculations with factor weights
  - Add WARNING level logging for data quality issues (NaN values, stale data)
  - Implement scan cycle summary logging with signals generated, rejected, and rejection reason breakdown
  - Create structured log format with timestamp, asset, timeframe, strategy, action, and details
  - _Requirements: 2.5, 10.1, 10.2, 10.3, 10.4, 10.5, 13.1, 13.2, 13.3, 13.4, 13.5_


- [x] 9. Implement liquidity and trading hours filtering

  - Add low-liquidity period detection (weekends, major holidays)
  - Implement trading hours validation per asset using config (XAU: London/NY sessions, US30: NY session)
  - Add logic to increase min_confluence_factors to 5 for XAU outside high-liquidity sessions
  - Implement volume moving average threshold check to suppress signals during low liquidity
  - Add logging for low-liquidity conditions with time until normal liquidity
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 10. Create Signal and MarketData data models


  - Implement Signal dataclass with all required fields (asset, timeframe, strategy, type, prices, timestamp)
  - Add quality metrics fields to Signal (confidence_score, confluence_factors, risk_reward_ratio)
  - Add market_data context field to Signal
  - Implement to_alert_message method on Signal to format trader alerts with confidence stars and key factors
  - Implement MarketData dataclass with price data and all indicators (RSI, ADX, EMAs, ATR, VWAP, volume)
  - Add volume_ratio property to MarketData
  - Implement validate method on MarketData to check for NaN or invalid values
  - _Requirements: 1.5, 2.4, 10.4, 13.4_

- [x] 11. Implement data validation and error handling


  - Create validate_market_data function to check for NaN values, missing data, and stale data
  - Implement safe_evaluate_signal wrapper with try-catch and validation checks
  - Add error logging with detailed information about which indicators failed validation
  - Implement configuration validation on startup with default fallback behavior
  - Add system administrator alerts when data errors persist for >10 cycles
  - _Requirements: 1.4, 13.1_

- [x] 12. Integrate Signal Quality Filter into main scanner flow


  - Update main scanner loop to call Signal Quality Filter after preliminary signal generation
  - Pass market data and preliminary signal to quality filter evaluate_signal method
  - Handle approved signals by creating Signal object and sending alert
  - Handle rejected signals by logging rejection reason and continuing scan
  - Add quality metrics to all signal alerts (confidence score, confluence factors, RR ratio)
  - Update signal storage to include recent_signals for duplicate detection
  - _Requirements: 1.5, 2.1, 2.3, 2.4, 7.1, 7.5, 14.5_


- [x] 13. Write integration tests for enhanced strategies


  - Create test cases for Momentum Shift Strategy with trend validation scenarios
  - Create test cases for Trend Alignment Strategy with various ADX values
  - Create test cases for EMA Cloud Breakout Strategy with breakout confirmation
  - Create test cases for Mean Reversion Strategy with reversal patterns
  - Create test cases for H4 HVG Strategy with gap validation
  - Mock market data with known conditions to verify signal generation or rejection
  - Verify log output contains expected rejection reasons
  - _Requirements: All strategy requirements_



- [x] 14. Write unit tests for Signal Quality Filter


  - Test confluence factor calculation for all 7 factors independently
  - Test confidence score calculation with various factor combinations
  - Test duplicate detection with time windows and price tolerance
  - Test risk-reward validation and score adjustments
  - Test edge cases (exact threshold values, boundary conditions)

  - _Requirements: 2.1, 2.2, 2.3, 7.1, 7.2, 7.3, 14.1, 14.2, 14.3_

- [x] 15. Write end-to-end tests for complete signal flow



  - Test US30 signal generation with valid momentum shift conditions
  - Test XAU/USD weak signal filtering (only 2 confluence factors)
  - Test BTC/USD duplicate prevention with similar signals
  - Test trend conflict detection (bullish RSI with price below EMA50)
  - Verify alert message formatting includes all quality metrics
  - Test configuration loading and asset-specific threshold application
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.4, 7.3, 10.4_
