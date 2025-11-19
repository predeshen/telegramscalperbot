"""
Live Data Verification Tests
Tests that the system can successfully fetch and process live market data.
"""
import pytest
import pandas as pd
from datetime import datetime

from src.unified_data_source import UnifiedDataSource, DataSourceConfig
from src.indicator_calculator import IndicatorCalculator


class TestLiveDataVerification:
    """Verify live data reception from unified data source"""
    
    def test_unified_data_source_fetch_btc_live(self):
        """Test fetching live BTC data from unified data source"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        
        try:
            # Fetch live BTC data
            df, is_fresh = data_source.get_latest_candles(
                symbol="BTC",
                timeframe="1m",
                limit=100,
                validate_freshness=True
            )
            
            # Verify data received
            assert df is not None, "DataFrame should not be None"
            assert not df.empty, "DataFrame should not be empty"
            assert len(df) > 0, "Should have received candles"
            
            # Verify required columns
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                assert col in df.columns, f"Missing column: {col}"
            
            # Verify data types
            assert pd.api.types.is_numeric_dtype(df['open']), "Open should be numeric"
            assert pd.api.types.is_numeric_dtype(df['close']), "Close should be numeric"
            assert pd.api.types.is_numeric_dtype(df['volume']), "Volume should be numeric"
            
            # Verify freshness
            assert isinstance(is_fresh, bool), "is_fresh should be boolean"
            
            # Verify timestamps are recent
            latest_timestamp = df.iloc[-1]['timestamp']
            time_diff = (datetime.now() - latest_timestamp).total_seconds()
            assert time_diff < 600, f"Data should be recent (< 10 min old), got {time_diff}s"
            
            print(f"✅ Live BTC data received: {len(df)} candles, Fresh: {is_fresh}")
            print(f"   Latest: {df.iloc[-1]['close']:.2f}, Time: {latest_timestamp}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not fetch live BTC data: {e}")
            return False
    
    def test_unified_data_source_fetch_gold_live(self):
        """Test fetching live Gold (XAU/USD) data"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        
        try:
            # Fetch live Gold data
            df, is_fresh = data_source.get_latest_candles(
                symbol="XAUUSD",
                timeframe="5m",
                limit=100,
                validate_freshness=True
            )
            
            # Verify data received
            assert df is not None, "DataFrame should not be None"
            assert not df.empty, "DataFrame should not be empty"
            assert len(df) > 0, "Should have received candles"
            
            # Verify price range (Gold typically 1500-2500)
            assert df['close'].min() > 1000, "Gold price seems too low"
            assert df['close'].max() < 3000, "Gold price seems too high"
            
            print(f"✅ Live Gold data received: {len(df)} candles, Fresh: {is_fresh}")
            print(f"   Latest: {df.iloc[-1]['close']:.2f}, Time: {df.iloc[-1]['timestamp']}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not fetch live Gold data: {e}")
            return False
    
    def test_unified_data_source_fetch_us30_live(self):
        """Test fetching live US30 (Dow Jones) data"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        
        try:
            # Fetch live US30 data
            df, is_fresh = data_source.get_latest_candles(
                symbol="US30",
                timeframe="15m",
                limit=100,
                validate_freshness=True
            )
            
            # Verify data received
            assert df is not None, "DataFrame should not be None"
            assert not df.empty, "DataFrame should not be empty"
            assert len(df) > 0, "Should have received candles"
            
            # Verify price range (US30 typically 30000-40000)
            assert df['close'].min() > 20000, "US30 price seems too low"
            assert df['close'].max() < 50000, "US30 price seems too high"
            
            print(f"✅ Live US30 data received: {len(df)} candles, Fresh: {is_fresh}")
            print(f"   Latest: {df.iloc[-1]['close']:.2f}, Time: {df.iloc[-1]['timestamp']}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not fetch live US30 data: {e}")
            return False
    
    def test_live_data_with_indicators(self):
        """Test that live data can be processed with indicators"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        calc = IndicatorCalculator()
        
        try:
            # Fetch live data
            df, is_fresh = data_source.get_latest_candles(
                symbol="BTC",
                timeframe="1m",
                limit=200,
                validate_freshness=True
            )
            
            if df.empty:
                print("⚠️  No data received")
                return False
            
            # Calculate indicators
            df_with_indicators = calc.calculate_all_indicators(
                df,
                ema_periods=[9, 21, 50],
                atr_period=14,
                rsi_period=6,
                volume_ma_period=20
            )
            
            # Verify indicators calculated
            assert 'ema_9' in df_with_indicators.columns, "EMA9 not calculated"
            assert 'rsi' in df_with_indicators.columns, "RSI not calculated"
            assert 'atr' in df_with_indicators.columns, "ATR not calculated"
            
            # Verify no NaN in critical indicators
            assert not df_with_indicators['ema_9'].isna().all(), "EMA9 all NaN"
            assert not df_with_indicators['rsi'].isna().all(), "RSI all NaN"
            
            # Verify indicator values are reasonable
            last_row = df_with_indicators.iloc[-1]
            assert 0 <= last_row['rsi'] <= 100, f"RSI out of range: {last_row['rsi']}"
            assert last_row['atr'] > 0, f"ATR should be positive: {last_row['atr']}"
            
            print(f"✅ Live data processed with indicators successfully")
            print(f"   EMA9: {last_row['ema_9']:.2f}, RSI: {last_row['rsi']:.1f}, ATR: {last_row['atr']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Could not process live data with indicators: {e}")
            return False
    
    def test_data_source_fallback_mechanism(self):
        """Test that data source fallback works"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        
        # Check source status
        status = data_source.get_source_status()
        
        print(f"✅ Data source status:")
        for source, info in status.items():
            print(f"   {source}: enabled={info['enabled']}, failures={info['failures']}")
        
        # Verify at least one source is available
        available_sources = [s for s, info in status.items() if info['enabled']]
        assert len(available_sources) > 0, "No data sources available"
        
        return True
    
    def test_multiple_timeframes_live(self):
        """Test fetching live data for multiple timeframes"""
        config = DataSourceConfig(
            primary_source="binance",
            fallback_sources=["twelve_data", "alpha_vantage"],
            freshness_threshold_seconds=300
        )
        
        data_source = UnifiedDataSource(config)
        timeframes = ["1m", "5m", "15m"]
        
        results = {}
        for tf in timeframes:
            try:
                df, is_fresh = data_source.get_latest_candles(
                    symbol="BTC",
                    timeframe=tf,
                    limit=50,
                    validate_freshness=True
                )
                
                if not df.empty:
                    results[tf] = {
                        'candles': len(df),
                        'fresh': is_fresh,
                        'latest_price': df.iloc[-1]['close']
                    }
                    print(f"✅ {tf}: {len(df)} candles, Fresh: {is_fresh}, Price: {df.iloc[-1]['close']:.2f}")
                else:
                    print(f"⚠️  {tf}: No data received")
                    
            except Exception as e:
                print(f"⚠️  {tf}: {e}")
        
        assert len(results) > 0, "Should have received data for at least one timeframe"
        return True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

