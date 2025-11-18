# Implementation Plan

- [x] 1. Update configuration files with relaxed thresholds



  - Update global signal_rules in all config files (config.json, config_multitime.json, us30_config.json, multi_crypto_scalp.json, multi_crypto_swing.json, multi_fx_scalp.json, multi_mixed.json)
  - Set volume_spike_threshold to 1.3 (from 1.5)
  - Set rsi_min to 25 (from 30)
  - Set rsi_max to 75 (from 70)
  - Set adx_min_trend_alignment to 15 (from 19)
  - Set duplicate_time_window_minutes to 10 (from 5)
  - Set duplicate_price_threshold_percent to 1.0 (from 0.5)
  - Add quality_filter section with min_confluence_factors=3, min_confidence_score=3, min_risk_reward=1.2
  - Add asset_specific section with BTC, XAUUSD, US30 overrides
  - Add diagnostics section with enabled=true, log_detection_attempts=true
  - Add bypass_mode section with enabled=false, auto_disable_after_hours=2
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2, 6.3, 9.1, 9.2_

- [x] 2. Create diagnostic system module


- [x] 2.1 Create src/signal_diagnostics.py with SignalDiagnostics class


  - Implement __init__ with scanner_name, detection_attempts, successful_detections, filter_rejections, data_quality_issues tracking
  - Implement log_detection_attempt(strategy, success, reason) method
  - Implement log_data_quality_issue(issue_type) method
  - Implement generate_report() method that returns formatted diagnostic report
  - Implement get_recommendations() method that analyzes data and returns actionable recommendations
  - Implement to_telegram_message() method for daily summary formatting
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.1, 7.2, 7.3_

- [x] 2.2 Create src/config_validator.py with ConfigValidator class


  - Implement REASONABLE_BOUNDS dictionary with parameter ranges
  - Implement validate_config(config) method that checks all parameters
  - Implement _get_nested_value() helper for accessing nested config values
  - Return list of warning messages for out-of-bounds values
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 9.5_

- [x] 2.3 Create src/bypass_mode.py with BypassMode class


  - Implement __init__ with config and alerter
  - Implement enable() method that sets enabled flag and sends notification
  - Implement disable() method that clears flag and sends notification
  - Implement check_auto_disable() method that disables after timeout
  - Implement should_bypass_filters() method that returns current state
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 3. Update SignalDetector with diagnostic logging



  - Add diagnostics parameter to __init__ (optional SignalDiagnostics instance)
  - Update detect_signals() to log each strategy attempt with pass/fail
  - Add try-except around each strategy call to log errors
  - Log successful detections with strategy name
  - Log failed detections with reason (pattern not met, error, etc.)
  - _Requirements: 1.2, 7.1, 7.2_

- [x] 4. Update strategy detection methods with relaxed thresholds


- [x] 4.1 Update _detect_ema_crossover() method


  - Remove EMA50 cascade requirement (only check EMA9 vs EMA21)
  - Use asset-specific volume threshold from config (default 1.3x)
  - Use asset-specific RSI range from config (default 25-75)
  - Add detailed debug logging for threshold checks
  - _Requirements: 3.1, 3.5, 4.1, 4.2_


- [x] 4.2 Update _detect_trend_alignment() method


  - Use asset-specific ADX minimum from config (default 15)
  - Use asset-specific volume threshold for trend_alignment (default 0.8x)
  - Remove strict EMA cascade requirement
  - Add detailed debug logging for threshold checks
  - _Requirements: 3.3, 4.5, 9.1, 9.2_

- [x] 4.3 Update _detect_mean_reversion() method




  - Reduce overextension threshold from 1.8 ATR to 1.5 ATR
  - Use asset-specific volume threshold for mean_reversion (default 1.5x)
  - Expand RSI extremes to <20 or >80 (from <25 or >75)
  - Add detailed debug logging for threshold checks
  - _Requirements: 3.2, 4.3_

- [x] 4.4 Update _detect_ema_cloud_breakout() method



  - Use asset-specific volume threshold for breakout (default 1.3x)
  - Expand RSI range to 30-70 (from 35-65)
  - Add detailed debug logging for threshold checks
  - _Requirements: 3.4, 4.4_


- [x] 4.5 Update _detect_momentum_shift() method


  - Reduce RSI momentum threshold from 60 to 55
  - Use asset-specific ADX minimum (default 15)
  - Use asset-specific volume threshold for momentum_shift (default 1.3x)
  - Add detailed debug logging for threshold checks
  - _Requirements: 3.5, 4.1_

- [x] 5. Update SignalQualityFilter with relaxed thresholds



- [x] 5.1 Update QualityConfig dataclass defaults


  - Set min_confluence_factors to 3 (from 4)
  - Set min_confidence_score to 3 (from 4)
  - Set duplicate_window_seconds to 600 (from 300)
  - Set duplicate_price_tolerance_pct to 1.0 (from 0.5)
  - Set significant_price_move_pct to 1.5 (from 1.0)
  - Set min_risk_reward to 1.2 (from 1.5)
  - _Requirements: 2.1, 2.2, 2.3, 5.1, 5.2_

- [x] 5.2 Add diagnostic logging to evaluate_signal() method


  - Add diagnostics parameter to __init__ (optional SignalDiagnostics instance)
  - Log detailed rejection reasons with missing confluence factors
  - Log confidence score calculation details
  - Log risk-reward validation results
  - Log duplicate detection results
  - Call diagnostics.log_detection_attempt() for each filter check
  - _Requirements: 1.3, 7.2, 7.3_

- [x] 5.3 Update check_duplicate() method with relaxed rules


  - Allow new signal if timeframe differs from previous signal
  - Allow new signal if RSI changed by more than 15 points
  - Use increased price tolerance (1.0% from 0.5%)
  - Use increased time window (10 minutes from 5 minutes)
  - Add detailed debug logging for duplicate checks
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Add data quality validation




- [x] 6.1 Add validate_data_quality() method to SignalDetector


  - Check minimum candle count (50)
  - Check for NaN values in critical indicators (close, volume, ema_9, ema_21, rsi, atr)
  - Check timestamp freshness (within 2x expected interval)
  - Check volume validity (> 0)
  - Return (is_valid, issues) tuple
  - Log data quality issues to diagnostics
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 6.2 Call validate_data_quality() in detect_signals() before strategy detection


  - Skip signal detection if data quality check fails
  - Log data quality issues
  - Continue to next iteration without crashing
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 7. Integrate diagnostic system into scanner applications


- [x] 7.1 Update main.py (BTC Scalp Scanner)


  - Import SignalDiagnostics, ConfigValidator, BypassMode
  - Create SignalDiagnostics instance with scanner_name="BTC-Scalp"
  - Create ConfigValidator and validate config on startup
  - Create BypassMode instance
  - Pass diagnostics to SignalDetector and SignalQualityFilter
  - Generate and send diagnostic report every 24 hours
  - Check bypass mode auto-disable in main loop
  - Send alert if no signals for 4 hours
  - _Requirements: 1.1, 1.4, 6.1, 6.4, 7.4, 7.5, 8.1, 8.5_

- [x] 7.2 Update main_swing.py (BTC Swing Scanner)

  - Import SignalDiagnostics, ConfigValidator, BypassMode
  - Create SignalDiagnostics instance with scanner_name="BTC-Swing"
  - Create ConfigValidator and validate config on startup
  - Create BypassMode instance
  - Pass diagnostics to SignalDetector and SignalQualityFilter
  - Generate and send diagnostic report every 24 hours
  - Check bypass mode auto-disable in main loop
  - Send alert if no signals for 4 hours
  - _Requirements: 1.1, 1.4, 6.1, 6.4, 7.4, 7.5, 8.1, 8.5_

- [x] 7.3 Update main_us30.py (US30 Momentum Scanner)

  - Import SignalDiagnostics, ConfigValidator, BypassMode
  - Create SignalDiagnostics instance with scanner_name="US30-Momentum"
  - Create ConfigValidator and validate config on startup
  - Create BypassMode instance
  - Pass diagnostics to SignalDetector and SignalQualityFilter
  - Generate and send diagnostic report every 24 hours
  - Check bypass mode auto-disable in main loop
  - Send alert if no signals for 4 hours
  - _Requirements: 1.1, 1.4, 6.1, 6.4, 7.4, 7.5, 8.1, 8.5_

- [x] 7.4 Update main_multi_symbol.py (Multi-Symbol Scanner)

  - Import SignalDiagnostics, ConfigValidator, BypassMode
  - Create SignalDiagnostics instance per symbol
  - Create ConfigValidator and validate config on startup
  - Create BypassMode instance
  - Pass diagnostics to each SymbolScanner
  - Generate and send diagnostic report every 24 hours (aggregated)
  - Check bypass mode auto-disable in main loop
  - Send alert if no signals for 4 hours per symbol
  - _Requirements: 1.1, 1.4, 6.1, 6.4, 7.4, 7.5, 8.1, 8.5_

- [x] 8. Update asset-specific scanner configurations

- [x] 8.1 Update xauusd_scanner/config_gold.json and config_gold_swing.json

  - Add asset_specific.XAUUSD section with volume thresholds
  - Add quality_filter section with relaxed thresholds
  - Add diagnostics section
  - Add bypass_mode section
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 8.2 Update us30_scanner/config_us30_scalp.json and config_us30_swing.json

  - Add asset_specific.US30 section with volume thresholds
  - Add quality_filter section with relaxed thresholds
  - Add diagnostics section
  - Add bypass_mode section
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 9. Add configuration logging on startup

  - Log active configuration source (global vs asset-specific) for each parameter
  - Log all threshold values being used
  - Log validation warnings if any
  - Log diagnostic system status (enabled/disabled)
  - Log bypass mode status
  - _Requirements: 6.4, 9.4_

- [x] 10. Implement daily diagnostic summary

- [x] 10.1 Add schedule_daily_summary() method to scanner applications

  - Calculate time until next 18:00 UTC
  - Schedule diagnostic report generation
  - Format report using DiagnosticReport.to_telegram_message()
  - Send via Telegram alerter
  - _Requirements: 7.4_

- [x] 10.2 Add check_no_signals_alert() method to scanner applications

  - Track time since last signal
  - If > 4 hours, send alert via Telegram
  - Include diagnostic summary in alert
  - Reset timer when signal is generated
  - _Requirements: 7.5_

- [x] 11. Create diagnostic CLI tool

  - Create scripts/diagnose_scanners.py script
  - Load configuration for all 8 scanners
  - Run diagnostic analysis on each
  - Generate comprehensive report
  - Output recommendations for threshold adjustments
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 12. Add unit tests for new components

  - Test ConfigValidator with various config scenarios
  - Test SignalDiagnostics logging and report generation
  - Test BypassMode enable/disable and auto-disable
  - Test relaxed duplicate detection rules
  - Test data quality validation
  - _Requirements: All_

- [x] 13. Add integration tests

  - Test end-to-end signal flow with relaxed thresholds
  - Test diagnostic logging throughout signal pipeline
  - Test daily summary generation
  - Test no-signals alert triggering
  - Test bypass mode integration
  - _Requirements: All_

- [x] 14. Update documentation


  - Update README.md with new configuration options
  - Document asset-specific configuration overrides
  - Document diagnostic system usage
  - Document bypass mode usage and safety
  - Add troubleshooting section with common issues
  - _Requirements: 6.1, 6.2, 8.1, 8.2, 8.3, 8.4_
