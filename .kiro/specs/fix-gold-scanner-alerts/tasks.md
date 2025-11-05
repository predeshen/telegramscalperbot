# Implementation Plan

- [x] 1. Add symbol attribute to base Signal class


  - Modify `src/signal_detector.py` to add `symbol: str = "BTC/USD"` field to Signal dataclass
  - This provides backward compatibility for BTC scanner
  - _Requirements: 1.3_

- [x] 2. Update GoldSignalDetector to accept and propagate symbol parameter

  - [x] 2.1 Modify `detect_signals()` method signature to accept `symbol` parameter with default "XAU/USD"


    - Update method in `xauusd_scanner/gold_signal_detector.py`
    - Pass symbol to all internal strategy detection methods
    - _Requirements: 1.3_
  
  - [x] 2.2 Update all strategy detection methods to accept symbol parameter


    - Modify `_detect_momentum_shift()` to accept `symbol` parameter
    - Modify `_detect_asian_range_breakout()` to accept `symbol` parameter
    - Modify `_detect_ema_cloud_breakout()` to accept `symbol` parameter
    - Modify `_detect_mean_reversion()` to accept `symbol` parameter
    - Modify `_detect_trend_following()` to accept `symbol` parameter
    - Each method should pass `symbol=symbol` when calling `_create_gold_signal()`
    - _Requirements: 1.3_
  
  - [x] 2.3 Complete the `_create_gold_signal()` method implementation


    - Read the complete method from the file (it was truncated)
    - Add `symbol` parameter to method signature
    - Set `signal.symbol = symbol` on the created GoldSignal object
    - _Requirements: 1.3, 1.4_

- [x] 3. Verify main_gold.py passes symbol correctly


  - Check that line 237 in `xauusd_scanner/main_gold.py` calls `detect_signals(candles, timeframe, symbol="XAU/USD")`
  - Ensure the symbol parameter is passed consistently throughout the scanning loop
  - _Requirements: 1.1, 1.2_

- [x] 4. Add data source transparency to configuration and alerts

  - [x] 4.1 Update Gold scanner configuration


    - Add `data_source`, `data_source_note` fields to `xauusd_scanner/config_gold.json`
    - Document that Yahoo Finance (GC=F) is used and may differ from spot prices
    - _Requirements: 2.1, 3.1_
  
  - [x] 4.2 Enhance startup message with data source information


    - Modify startup message in `xauusd_scanner/main_gold.py` to include data source
    - Add note about potential price variance from broker
    - _Requirements: 2.2, 3.2, 3.4_
  
  - [x] 4.3 Add data source logging on initialization


    - Log the data source (Yahoo Finance - GC=F) when Gold scanner starts
    - Include in the initialization log messages
    - _Requirements: 3.3_

- [x] 5. Verify alert formatting uses correct symbol


  - Review `src/alerter.py` TelegramAlerter `_format_signal_message()` method
  - Confirm it uses `getattr(signal, 'symbol', 'BTC/USD')` correctly
  - Test that once symbol is set, alerts show "XAU/USD LONG SIGNAL" instead of "BTC/USD"
  - _Requirements: 1.1, 1.2, 1.4_

- [x] 6. Test the complete signal flow


  - [x] 6.1 Run Gold scanner with test data

    - Start the Gold scanner
    - Wait for a signal to be generated
    - Capture the signal object and verify symbol="XAU/USD"
    - _Requirements: 1.3_
  
  - [x] 6.2 Verify Telegram alert shows correct symbol

    - Check that the Telegram message header shows "XAU/USD" not "BTC/USD"
    - Verify the alert formatting is correct
    - _Requirements: 1.1, 1.2_
  
  - [x] 6.3 Verify startup message includes data source

    - Check that startup message mentions "Yahoo Finance (GC=F)"
    - Verify price variance disclaimer is present
    - _Requirements: 2.2, 3.2_

- [x] 7. Create documentation for price variance


  - [x] 7.1 Add README section explaining data sources


    - Document that Gold scanner uses Yahoo Finance Gold Futures (GC=F)
    - Explain typical price variance from spot XAU/USD (0.1-0.5%)
    - Note that traders should reference their broker prices for actual entry/exit
    - _Requirements: 2.4, 3.1_
  
  - [x] 7.2 Add troubleshooting guide for price differences


    - Create section in `xauusd_scanner/README.md` about price variance
    - Explain why prices differ (futures vs spot)
    - Provide guidance on how to interpret signals with price differences
    - _Requirements: 2.1, 2.4_
