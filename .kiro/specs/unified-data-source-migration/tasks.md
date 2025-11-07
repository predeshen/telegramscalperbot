# Implementation Plan

- [x] 1. Implement Unified Data Source Layer


  - Create UnifiedDataSource class in src/unified_data_source.py with YFinance integration
  - Implement symbol mapping (BTC -> BTC-USD, XAUUSD -> GC=F, US30 -> ^DJI)
  - Add connection retry logic with exponential backoff
  - Add error handling for connection failures
  - _Requirements: 1.1, 1.2, 1.5_

- [x] 2. Implement Price Validation


  - Create PriceValidator class in src/price_validator.py
  - Implement price change validation (0.5% normal threshold, 5% anomaly threshold)
  - Implement volume validation (reject zero/negative volume)
  - Implement timestamp validation (reject future timestamps or >1hr old)
  - Implement OHLC relationship validation
  - _Requirements: 1.4, 5.1, 5.2, 5.3, 5.4_

- [x] 3. Implement Symbol Context Management


  - Create SymbolContext class in src/symbol_context.py
  - Add symbol validation (not null/empty)
  - Add emoji mapping for each asset (₿ for BTC, 🥇 for Gold, 📊 for US30)
  - Update Signal class to include SymbolContext as required field
  - Add validation in Signal.__post_init__ to ensure symbol context is valid
  - _Requirements: 2.1, 2.5, 6.4_

- [x] 4. Update Signal Detector to Include Symbol Context


  - Update src/signal_detector.py to accept and propagate symbol parameter
  - Ensure all signal creation includes SymbolContext
  - Update xauusd_scanner/gold_signal_detector.py to use SymbolContext
  - Update us30_scanner signal detectors to use SymbolContext
  - _Requirements: 2.1, 2.3_

- [x] 5. Implement Signal Quality Filter



  - Create SignalQualityFilter class in src/signal_quality_filter.py
  - Implement confluence factor evaluation (trend, volume, momentum, support/resistance, multi-timeframe)
  - Implement confidence score calculation (1-5 scale based on confluence factors)
  - Implement duplicate detection within 5-minute time window
  - Add signal suppression logging with reasons
  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 6. Implement Asset-Specific Alert Formatters


  - Create AssetSpecificAlerter class in src/asset_specific_alerter.py
  - Implement BTCAlertFormatter with BTC-specific context (dominance if available)
  - Implement GoldAlertFormatter with Gold-specific context (session, spread, key levels)
  - Implement US30AlertFormatter with US30-specific context (market hours, trend strength)
  - Ensure all formatters include confidence score and proper price precision (2 decimals)
  - Add disclaimer about indicative pricing vs broker execution prices
  - _Requirements: 1.3, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7. Migrate News Calendar to Shared Component


  - Move xauusd_scanner/news_calendar.py to src/news_calendar.py
  - Move xauusd_scanner/news_events.json to config/news_events.json
  - Update NewsCalendar to be asset-agnostic (remove Gold-specific references)
  - Update xauusd_scanner imports to use src/news_calendar.py
  - _Requirements: 5.5 (indirectly - prevents bad signals during volatile news)_

- [x] 8. Integrate News Calendar into BTC Scanner


  - Update main.py (BTC scalp scanner) to import and use NewsCalendar
  - Add news pause check in main scanning loop
  - Add news status to startup notification
  - Add alerts when trading pauses/resumes due to news
  - _Requirements: 5.5 (indirectly)_

- [x] 9. Integrate News Calendar into US30 Scanners

  - Update us30_scanner/main_us30_scalp.py to import and use NewsCalendar
  - Update us30_scanner/main_us30_swing.py to import and use NewsCalendar
  - Add news pause check in main scanning loops
  - Add news status to startup notifications
  - Add alerts when trading pauses/resumes due to news
  - _Requirements: 5.5 (indirectly)_


- [x] 10. Implement Configuration Manager

  - Create ConfigurationManager class in src/config_manager.py
  - Implement config loading with validation
  - Implement validation for required fields (data_source.provider, symbol_map, scanners)
  - Implement hot-reload functionality (check file modification time)
  - Add fail-fast error handling with clear error messages
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_


- [ ] 11. Migrate BTC Scalp Scanner to Unified Data Source
  - Update main.py to use UnifiedDataSource instead of Kraken/Binance clients
  - Update symbol references to use internal symbol (BTC) with YF mapping (BTC-USD)
  - Add PriceValidator integration
  - Test price accuracy against MT5 broker prices
  - _Requirements: 1.1, 1.2, 1.4_


- [ ] 12. Update All Scanners to Use Symbol Context
  - Update main.py (BTC) to pass symbol context to signal detector
  - Update main_swing.py (BTC swing) to pass symbol context
  - Update xauusd_scanner/main_gold.py to pass symbol context
  - Update xauusd_scanner/main_gold_swing.py to pass symbol context
  - Update us30_scanner/main_us30_scalp.py to pass symbol context
  - Update us30_scanner/main_us30_swing.py to pass symbol context
  - Verify symbol appears correctly in all log messages

  - _Requirements: 2.2, 2.4_

- [ ] 13. Integrate Signal Quality Filter into All Scanners
  - Update main.py (BTC scalp) to use SignalQualityFilter before sending alerts
  - Update main_swing.py (BTC swing) to use SignalQualityFilter
  - Update xauusd_scanner scanners to use SignalQualityFilter
  - Update us30_scanner scanners to use SignalQualityFilter

  - Ensure signals below confidence threshold (3) are rejected and logged
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ] 14. Update Alerter to Use Asset-Specific Formatters
  - Update src/alerter.py to use AssetSpecificAlerter
  - Ensure all scanners use the new alerter with asset-specific formatting

  - Verify alerts include correct emoji, symbol, and asset-specific context
  - Verify price precision is correct (2 decimals for all assets)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 15. Implement Multi-Scanner Coordinator
  - Create MultiScannerCoordinator class in src/multi_scanner_coordinator.py
  - Implement alert queue with timestamp-based priority

  - Implement 30-second minimum gap enforcement between alerts
  - Implement signal rate monitoring (5 signals/hour threshold)
  - Add warning logs for excessive signal generation
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 16. Implement Health Monitor
  - Create HealthMonitor class in src/health_monitor.py

  - Implement data quality issue tracking per scanner
  - Implement 3 consecutive failures threshold for scanner pause
  - Implement scanner pause/resume functionality
  - Add administrator alert functionality for critical issues
  - _Requirements: 5.5, 7.4_


- [ ] 17. Integrate Health Monitor into All Scanners
  - Update all scanner main files to use HealthMonitor
  - Add health status reporting to heartbeat messages
  - Add data quality issue recording on validation failures
  - Test scanner pause after 3 consecutive failures
  - _Requirements: 5.5, 7.4, 7.5_

- [x] 18. Update Configuration Files

  - Create unified config schema in config/unified_config.json
  - Update config/config.json (BTC) with data_source section
  - Update config/config_multitime.json (BTC swing) with data_source section
  - Update config/us30_config.json with data_source section
  - Update xauusd_scanner configs with data_source section
  - Add news_calendar_file path to all configs

  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 19. Add Integration Points for Coordinator
  - Update all scanner main files to register with MultiScannerCoordinator
  - Route all alerts through coordinator's alert queue
  - Add coordinator health status to heartbeat messages
  - Test alert gap enforcement across multiple scanners
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 20. End-to-End Testing and Validation

  - Test BTC scanner with unified data source and verify prices match MT5
  - Test symbol context propagation through entire pipeline for all assets
  - Test news calendar pause functionality across all scanners
  - Test signal quality filter with various confluence scenarios
  - Test alert formatting for all three assets (BTC, Gold, US30)
  - Test multi-scanner coordination with simultaneous signals
  - Test health monitor pause after 3 data quality failures
  - Verify all alerts include correct symbol, emoji, and asset-specific context
  - _Requirements: All requirements (1.1-7.5)_
