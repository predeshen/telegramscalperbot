"""
Live Data Integration Tests
Tests the entire pipeline with real data from Yahoo Finance
"""
import pytest
import pandas as pd
from datetime import datetime, time as dt_time
import logging

from src.unified_data_source import UnifiedDataSource, DataSourceConfig
from src.price_validator import PriceValidator, ValidationConfig
from src.indicator_calculator import IndicatorCalculator
from src.signal_detector import SignalDetector
from src.symbol_context import SymbolContext

logger = logging.getLogger(__name__)


def is_market_open() -> bool:
    """Check if markets are likely open (rough check)."""
    now = datetime.now()
    # Markets are generally open Mon-Fri
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    return True


@pytest.mark.skipif(not is_market_open(), reason="Markets are closed on weekends")
class TestLiveDataIntegration:
    """Test with real live data from Yahoo Finance."""
    
    def test_fetch_btc_live_data(self):
        """Test fetching real BTC data from Yahoo Finance."""
        # Initialize unified data source
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        
        # Connect to BTC
        success = data_source.connect("BTC", ["1h", "4h"])
        assert success, "Failed to connect to data source for BTC"
        
        # Fetch 1-hour data
        df = data_source.fetch_ohlcv("BTC", "1h", limit=500)
        
        # Verify we got data
        assert not df.empty, "Received empty DataFrame for BTC 1h"
        assert len(df) >= 200, f"Insufficient data: got {len(df)} rows, need at least 200"
        
        # Verify required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"
        
        # Verify symbol context
        assert df['symbol'].iloc[0] == "BTC"
        
        logger.info(f"✅ Successfully fetched {len(df)} BTC candles")
        logger.info(f"   Latest price: ${df['close'].iloc[-1]:,.2f}")
        logger.info(f"   Latest timestamp: {df['timestamp'].iloc[-1]}")
    
    def test_fetch_gold_live_data(self):
        """Test fetching real Gold data from Yahoo Finance."""
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        
        # Connect to Gold
        success = data_source.connect("XAUUSD", ["1h", "4h"])
        assert success, "Failed to connect to data source for Gold"
        
        # Fetch 1-hour data
        df = data_source.fetch_ohlcv("XAUUSD", "1h", limit=500)
        
        # Verify we got data
        assert not df.empty, "Received empty DataFrame for Gold 1h"
        assert len(df) >= 200, f"Insufficient data: got {len(df)} rows, need at least 200"
        
        # Verify symbol context
        assert df['symbol'].iloc[0] == "XAUUSD"
        
        logger.info(f"✅ Successfully fetched {len(df)} Gold candles")
        logger.info(f"   Latest price: ${df['close'].iloc[-1]:,.2f}")
    
    def test_fetch_us30_live_data(self):
        """Test fetching real US30 data from Yahoo Finance."""
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        
        # Connect to US30
        success = data_source.connect("US30", ["1h", "4h"])
        assert success, "Failed to connect to data source for US30"
        
        # Fetch 1-hour data
        df = data_source.fetch_ohlcv("US30", "1h", limit=500)
        
        # Verify we got data (US30 may have limited historical data)
        assert not df.empty, "Received empty DataFrame for US30 1h"
        assert len(df) >= 50, f"Insufficient data: got {len(df)} rows, need at least 50"
        
        # Verify symbol context
        assert df['symbol'].iloc[0] == "US30"
        
        logger.info(f"✅ Successfully fetched {len(df)} US30 candles")
        logger.info(f"   Latest price: ${df['close'].iloc[-1]:,.2f}")
        
        # Note: US30 may have limited historical data compared to crypto pairs
        if len(df) < 200:
            logger.warning(f"⚠️  US30 has limited historical data ({len(df)} rows)")
    
    def test_price_validation_with_live_data(self):
        """Test price validation with real data."""
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        data_source.connect("BTC", ["1h"])
        
        df = data_source.fetch_ohlcv("BTC", "1h", limit=100)
        
        # Validate prices
        validator = PriceValidator(ValidationConfig())
        
        valid_count = 0
        warning_count = 0
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1]
            
            result = validator.validate_candle(current, previous)
            
            if result.is_valid:
                valid_count += 1
            if result.warnings:
                warning_count += 1
                logger.warning(f"Price validation warning at {current['timestamp']}: {result.warnings}")
        
        # Most candles should be valid
        validity_rate = valid_count / (len(df) - 1) * 100
        logger.info(f"✅ Price validation: {validity_rate:.1f}% valid, {warning_count} warnings")
        
        assert validity_rate > 95, f"Too many invalid candles: {validity_rate:.1f}%"
    
    def test_full_pipeline_with_live_data(self):
        """Test the complete pipeline: fetch → validate → indicators → signals."""
        # 1. Fetch data
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        data_source.connect("BTC", ["1h"])
        
        df = data_source.fetch_ohlcv("BTC", "1h", limit=500)
        logger.info(f"📊 Fetched {len(df)} candles")
        
        # 2. Validate data
        validator = PriceValidator()
        all_valid, results = validator.validate_dataframe(df)
        logger.info(f"✅ Validation: {sum(1 for r in results if r.is_valid)}/{len(results)} valid")
        
        # 3. Calculate indicators
        indicator_calc = IndicatorCalculator()
        df_with_indicators = indicator_calc.calculate_all_indicators(
            df,
            ema_periods=[9, 21, 50, 100, 200],
            atr_period=14,
            rsi_period=14,
            volume_ma_period=20
        )
        
        # Verify indicators were calculated
        assert 'ema_9' in df_with_indicators.columns
        assert 'ema_21' in df_with_indicators.columns
        assert 'rsi' in df_with_indicators.columns
        assert 'atr' in df_with_indicators.columns
        assert 'vwap' in df_with_indicators.columns
        
        # Check for NaN values (should be minimal, only at the start)
        nan_count = df_with_indicators['ema_200'].isna().sum()
        logger.info(f"📈 Indicators calculated, {nan_count} NaN values (expected at start)")
        
        # 4. Try to detect signals
        signal_detector = SignalDetector()
        signal = signal_detector.detect_signals(df_with_indicators, "1h", "BTC/USD")
        
        if signal:
            logger.info(f"🚨 Signal detected: {signal.signal_type} at ${signal.entry_price:,.2f}")
            logger.info(f"   Confidence: {signal.confidence}/5")
            logger.info(f"   Symbol context: {signal.symbol_context.get_formatted_name()}")
            
            # Verify signal has symbol context
            assert signal.symbol_context is not None
            assert signal.symbol_context.symbol == "BTC"
            assert signal.symbol_context.emoji == "₿"
        else:
            logger.info("ℹ️  No signal detected (this is normal)")
        
        logger.info("✅ Full pipeline test completed successfully")
    
    def test_h4_hvg_detection_with_live_data(self):
        """Test H4 HVG detection with real 4-hour data."""
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        data_source.connect("BTC", ["4h"])
        
        df = data_source.fetch_ohlcv("BTC", "4h", limit=500)
        logger.info(f"📊 Fetched {len(df)} 4h candles for H4 HVG detection")
        
        # Calculate indicators
        indicator_calc = IndicatorCalculator()
        df_with_indicators = indicator_calc.calculate_all_indicators(
            df,
            ema_periods=[9, 21, 50, 100, 200],
            atr_period=14,
            rsi_period=14,
            volume_ma_period=20
        )
        
        # Detect signals (H4 HVG should be checked on 4h timeframe)
        signal_detector = SignalDetector()
        signal = signal_detector.detect_signals(df_with_indicators, "4h", "BTC/USD")
        
        if signal and hasattr(signal, 'strategy') and signal.strategy == 'H4 HVG':
            logger.info(f"🔥 H4 HVG signal detected!")
            logger.info(f"   Type: {signal.signal_type}")
            logger.info(f"   Entry: ${signal.entry_price:,.2f}")
            if hasattr(signal, 'gap_info') and signal.gap_info:
                logger.info(f"   Gap: {signal.gap_info.gap_percent:.2f}%")
        else:
            logger.info("ℹ️  No H4 HVG signal detected (this is normal)")
        
        logger.info("✅ H4 HVG detection test completed")
    
    def test_all_symbols_simultaneously(self):
        """Test fetching data for all symbols at once."""
        config = DataSourceConfig()
        data_source = UnifiedDataSource(config)
        
        symbols = ["BTC", "XAUUSD", "US30"]
        results = {}
        
        for symbol in symbols:
            try:
                data_source.connect(symbol, ["1h"])
                df = data_source.fetch_ohlcv(symbol, "1h", limit=500)
                
                results[symbol] = {
                    'success': True,
                    'rows': len(df),
                    'latest_price': df['close'].iloc[-1],
                    'latest_time': df['timestamp'].iloc[-1]
                }
                
                logger.info(f"✅ {symbol}: {len(df)} candles, latest ${df['close'].iloc[-1]:,.2f}")
                
            except Exception as e:
                results[symbol] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"❌ {symbol}: {e}")
        
        # All symbols should succeed
        for symbol, result in results.items():
            assert result['success'], f"{symbol} failed: {result.get('error')}"
            # US30 may have limited historical data, so use lower threshold
            min_rows = 50 if symbol == "US30" else 200
            assert result['rows'] >= min_rows, f"{symbol} insufficient data: {result['rows']} (need {min_rows})"
        
        logger.info("✅ All symbols fetched successfully")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
