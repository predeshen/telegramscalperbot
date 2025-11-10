# Implementation Plan

- [x] 1. Create Strategy Helper Classes and Utilities


  - Create `src/strategy_helpers.py` with data models (MarketConditions, FibonacciLevels, SupportResistanceLevel)
  - Implement FibonacciCalculator class with swing detection and level calculation methods
  - Implement SupportResistanceFinder class with level identification and round number detection
  - Implement KeyLevelTracker class for tracking key price levels
  - _Requirements: 5.1, 5.2, 6.1, 6.2, 7.1_

- [x] 2. Create Strategy Registry System


  - Create `src/strategy_registry.py` with StrategyRegistry class
  - Implement strategy registration and retrieval methods
  - Implement asset-specific parameter loading from configuration
  - Implement enable/disable toggle checking per scanner
  - Add strategy metadata tracking (execution count, success rate)
  - _Requirements: 9.1, 9.2, 10.1, 10.2_

- [x] 3. Create Strategy Orchestrator



  - Create `src/strategy_orchestrator.py` with StrategyOrchestrator class
  - Implement market condition analysis (ADX, ATR, volatility detection)
  - Implement strategy selection logic based on market conditions
  - Implement strategy priority ordering (trending vs ranging markets)
  - Add conflict detection to reject contradictory signals
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

- [x] 4. Implement Fibonacci Retracement Strategy



  - Add `_detect_fibonacci_retracement()` method to SignalDetector class
  - Implement swing high/low identification logic
  - Calculate Fibonacci levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
  - Detect price proximity to Fibonacci levels (within 0.5%)
  - Validate reversal candle patterns at Fibonacci levels
  - Check volume confirmation (1.3x average minimum)
  - Detect RSI divergence for increased confidence
  - Set stop-loss beyond next Fibonacci level
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 5. Implement Support/Resistance Bounce Strategy



  - Add `_detect_support_resistance_bounce()` method to SignalDetector class
  - Implement historical support level identification (minimum 2 touches)
  - Implement historical resistance level identification (minimum 2 touches)
  - Detect price proximity to support/resistance (within 0.3%)
  - Validate reversal candle patterns (pin bar, engulfing, doji)
  - Check volume confirmation (1.4x average minimum)
  - Increase confidence for multiple touches (3+ touches)
  - Increase priority for round number alignment
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 6. Implement Key Level Break and Retest Strategy


  - Add `_detect_key_level_break_retest()` method to SignalDetector class
  - Identify key levels (round numbers, previous highs/lows, psychological levels)
  - Detect key level breaks with volume confirmation
  - Monitor for retest within 5-10 candles
  - Validate retest holds with volume (0.8x breakout volume minimum)
  - Generate continuation signal on successful retest
  - Require stronger confirmation for major round numbers (1.5x volume)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 7. Implement ADX + RSI + Momentum Confluence Strategy



  - Add `_detect_adx_rsi_momentum_confluence()` method to SignalDetector class
  - Check ADX threshold (> 20 for trend, > 25 for strong trend)
  - Detect RSI directional crosses (above/below 50)
  - Calculate RSI momentum acceleration (change > 3 points over 2 candles)
  - Validate price momentum alignment (higher highs for bullish, lower lows for bearish)
  - Check volume confirmation (1.2x average minimum)
  - Increase confidence when ADX is rising (strengthening trend)
  - Reject signals when ADX < 18 (market too flat)
  - Require additional confirmation when RSI in extreme zones (< 30 or > 70)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11_

- [x] 8. Unify Asian Range Breakout Strategy for All Assets

  - Add `_detect_asian_range_breakout()` method to SignalDetector class (if not exists)
  - Implement Asian session range tracking (high/low recording)
  - Detect breakout above Asian range high with volume confirmation
  - Detect breakout below Asian range low with volume confirmation
  - Implement retest detection and validation
  - Add asset-specific buffer parameters (0.3% for BTC, 2 pips for Gold, 15 points for US30)
  - Integrate with BTC scalp and swing scanners
  - Integrate with US30 scalp and swing scanners
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 9. Unify Liquidity Sweep Strategy for All Assets

  - Add `_detect_liquidity_sweep()` method to SignalDetector class (if not exists)
  - Detect price sweeps below recent swing lows (bullish setup)
  - Detect price sweeps above recent swing highs (bearish setup)
  - Require volume spike (1.5x average minimum)
  - Validate price closes back above/below VWAP
  - Check EMA alignment for reversal direction confirmation
  - Integrate with BTC scalp and swing scanners
  - Integrate with Gold scalp and swing scanners
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 10. Unify Trend Following Strategy for All Assets

  - Add `_detect_trend_following_pullback()` method to SignalDetector class (if not exists)
  - Implement swing point detection (minimum 3 swings for trend)
  - Detect pullback to EMA(21) in uptrends
  - Detect pullback to EMA(21) in downtrends
  - Reject pullbacks deeper than 61.8%
  - Validate bounce with volume confirmation (1.2x average minimum)
  - Check RSI range (40-80 for uptrends, 20-60 for downtrends)
  - Integrate with BTC scalp and swing scanners
  - Integrate with US30 scalp and swing scanners
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 11. Update Configuration Files with Strategy Settings





  - Add strategy configuration section to `config/config.json` (BTC)
  - Add strategy configuration section to `us30_scanner/config_us30_scalp.json`
  - Add strategy configuration section to `us30_scanner/config_us30_swing.json`
  - Add strategy configuration section to `xauusd_scanner/config_gold.json`
  - Add strategy configuration section to `xauusd_scanner/config_gold_swing.json`
  - Add asset-specific parameters for each strategy
  - Add enable/disable toggles for each strategy per scanner
  - Add strategy priority configuration for different market conditions
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 12. Integrate Strategy System with Scanners



  - Update SignalDetector.__init__() to accept StrategyRegistry and StrategyOrchestrator
  - Modify SignalDetector.detect_signals() to use strategy orchestration
  - Update BTC scalp scanner (main.py) to initialize new strategy system
  - Update BTC swing scanner (main_swing.py) to initialize new strategy system
  - Update Gold scalp scanner (xauusd_scanner/main_gold.py) to initialize new strategy system
  - Update Gold swing scanner (xauusd_scanner/main_gold_swing.py) to initialize new strategy system
  - Update US30 scalp scanner (us30_scanner/main_us30_scalp.py) to initialize new strategy system
  - Update US30 swing scanner (us30_scanner/main_us30_swing.py) to initialize new strategy system
  - Add feature flag `use_unified_strategies` to all configs (default: false for safety)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2_

- [x] 13. Add Strategy Metadata to Signal Class

  - Update Signal dataclass to include `strategy_metadata` field
  - Add metadata population for Fibonacci retracement signals
  - Add metadata population for support/resistance signals
  - Add metadata population for key level signals
  - Add metadata population for ADX+RSI+Momentum signals
  - Update signal serialization (to_dict) to include metadata
  - Update alert formatting to display strategy-specific details
  - _Requirements: 11.3_

- [x] 14. Implement Error Handling and Logging

  - Create StrategyError exception classes (InsufficientDataError, InvalidParametersError)
  - Add try-catch blocks around strategy detection calls
  - Implement graceful fallback when strategy fails
  - Add debug logging for strategy selection decisions
  - Add info logging for successful signal detection
  - Add performance logging (execution time per strategy)
  - Add warning logging for consistently failing strategies
  - _Requirements: 11.4, 11.5_

- [x] 15. Create Unit Tests for Helper Classes

  - Write tests for FibonacciCalculator (swing detection, level calculation)
  - Write tests for SupportResistanceFinder (level identification, round numbers)
  - Write tests for KeyLevelTracker (level tracking, break detection)
  - Write tests for MarketConditions analysis
  - Achieve 90%+ code coverage for helper classes

- [x] 16. Create Unit Tests for New Strategies

  - Write tests for Fibonacci retracement strategy (all acceptance criteria)
  - Write tests for support/resistance bounce strategy (all acceptance criteria)
  - Write tests for key level break & retest strategy (all acceptance criteria)
  - Write tests for ADX+RSI+Momentum strategy (all acceptance criteria)
  - Test edge cases (insufficient data, invalid parameters, extreme values)
  - Achieve 90%+ code coverage for new strategies

- [x] 17. Create Integration Tests for Unified Strategies

  - Write tests for Asian Range Breakout on BTC
  - Write tests for Asian Range Breakout on US30
  - Write tests for Liquidity Sweep on BTC
  - Write tests for Liquidity Sweep on Gold
  - Write tests for Trend Following on BTC
  - Write tests for Trend Following on US30
  - Verify asset-specific parameter adaptation works correctly

- [x] 18. Create Integration Tests for Strategy Orchestration

  - Write tests for strategy selection in trending markets (ADX > 25)
  - Write tests for strategy selection in ranging markets (ADX < 20)
  - Write tests for strategy selection in high volatility (ATR > 1.5x)
  - Write tests for strategy selection in low volatility (ATR < 0.8x)
  - Write tests for strategy priority ordering
  - Write tests for conflict detection and signal rejection
  - Verify correct strategy is selected for each market condition

- [x] 19. Performance Testing and Optimization

  - Measure strategy execution time for each strategy (target: < 100ms)
  - Measure full scan time with all strategies enabled (target: < 500ms)
  - Implement caching for Fibonacci levels (cache for 10 candles)
  - Implement caching for support/resistance levels (cache for 20 candles)
  - Optimize swing detection algorithm for performance
  - Profile and optimize bottlenecks
  - Verify memory usage remains acceptable (< 500MB per scanner)

- [x] 20. Documentation and Migration Guide

  - Update README.md with new strategy descriptions
  - Create STRATEGY_GUIDE.md with detailed strategy explanations
  - Document configuration options for each strategy
  - Create migration guide for enabling unified strategies
  - Document asset-specific parameter tuning guidelines
  - Add troubleshooting section for common issues
  - Create example configurations for different trading styles

- [x] 21. Gradual Rollout and Validation


  - Enable unified strategies on BTC scalp scanner with feature flag
  - Monitor signal quality for 24 hours, compare with baseline
  - Enable on BTC swing scanner, monitor for 24 hours
  - Enable on Gold scalp scanner, monitor for 24 hours
  - Enable on Gold swing scanner, monitor for 24 hours
  - Enable on US30 scalp scanner, monitor for 24 hours
  - Enable on US30 swing scanner, monitor for 24 hours
  - Collect performance metrics and signal quality data
  - Make final adjustments based on real-world performance
  - Set `use_unified_strategies: true` as default in all configs
