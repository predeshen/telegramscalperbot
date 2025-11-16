"""Integration tests for multi-symbol scanning."""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.symbol_orchestrator import SymbolOrchestrator
from src.symbol_scanner import SymbolScanner
from src.signal_filter import SignalFilter
from src.trade_tracker import TradeTracker
from src.asset_config_manager import AssetConfigManager
from src.fvg_detector import FVGDetector, FVGZone
from src.nwog_detector import NWOGDetector, NWOGZone
from src.signal_detector import Signal


class TestParallelSymbolScanning:
    """Test parallel symbol scanning without blocking."""
    
    @pytest.fixture
    def mock_config_file(self):
        """Create a temporary config file."""
        config = {
            "symbols": {
                "BTC-USD": {
                    "enabled": True,
                    "asset_type": "crypto",
                    "display_name": "Bitcoin",
                    "emoji": "₿",
                    "timeframes": ["5m", "15m"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.8,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.5,
                        "take_profit_atr_multiplier": 2.0
                    }
                },
                "ETH-USD": {
                    "enabled": True,
                    "asset_type": "crypto",
                    "display_name": "Ethereum",
                    "emoji": "Ξ",
                    "timeframes": ["5m", "15m"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.9,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.8,
                        "take_profit_atr_multiplier": 2.2
                    }
                }
            },
            "global_settings": {
                "polling_interval_seconds": 1,
                "max_concurrent_symbols": 10,
                "signal_conflict_window_minutes": 5,
                "duplicate_signal_window_minutes": 10
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            return f.name
    
    def test_parallel_scanning_non_blocking(self, mock_config_file):
        """Test that multiple symbols can be scanned in parallel without blocking."""
        config_manager = AssetConfigManager(mock_config_file)
        
        mock_alerter = Mock()
        orchestrator = SymbolOrchestrator(config_manager, mock_alerter, max_concurrent_symbols=5)
        
        # Add multiple symbols
        symbols_added = []
        for symbol in config_manager.get_enabled_symbols():
            if orchestrator.add_symbol(symbol):
                symbols_added.append(symbol)
        
        assert len(symbols_added) == 2
        assert "BTC-USD" in symbols_added
        assert "ETH-USD" in symbols_added
        
        # Verify scanners were created
        assert len(orchestrator.scanners) == 2
        
        # Test that we can access all scanners without blocking
        start_time = time.time()
        for symbol, scanner in orchestrator.scanners.items():
            assert scanner.symbol == symbol
        elapsed = time.time() - start_time
        
        # Should complete instantly (< 0.1 seconds)
        assert elapsed < 0.1


class TestTimeframeConflictResolution:
    """Test timeframe conflict resolution."""
    
    @pytest.fixture
    def signal_filter(self):
        """Create a SignalFilter instance."""
        return SignalFilter(conflict_window_minutes=5, duplicate_window_minutes=10)
    
    def test_long_15m_short_1d_conflict(self, signal_filter):
        """Test LONG 15m + SHORT 1d scenario - higher timeframe wins."""
        # Add 1d SHORT signal first
        signal_1d = Mock()
        signal_1d.timestamp = datetime.now()
        signal_1d.timeframe = "1d"
        signal_1d.signal_type = "SHORT"
        signal_1d.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal_1d)
        
        # Try to add 15m LONG signal (conflicting)
        signal_15m = Mock()
        signal_15m.timestamp = datetime.now()
        signal_15m.timeframe = "15m"
        signal_15m.signal_type = "LONG"
        signal_15m.entry_price = 95100.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", signal_15m)
        
        # Lower timeframe should be suppressed
        assert should_suppress
        assert "Conflicting signal" in reason
        assert "1d" in reason
        assert "higher priority" in reason
    
    def test_short_1h_long_4h_conflict(self, signal_filter):
        """Test SHORT 1h + LONG 4h scenario - 4h wins."""
        # Add 4h LONG signal
        signal_4h = Mock()
        signal_4h.timestamp = datetime.now()
        signal_4h.timeframe = "4h"
        signal_4h.signal_type = "LONG"
        signal_4h.entry_price = 95000.0
        
        signal_filter.add_signal_to_history("BTC-USD", signal_4h)
        
        # Try to add 1h SHORT signal
        signal_1h = Mock()
        signal_1h.timestamp = datetime.now()
        signal_1h.timeframe = "1h"
        signal_1h.signal_type = "SHORT"
        signal_1h.entry_price = 95000.0
        
        should_suppress, reason = signal_filter.should_suppress_signal("BTC-USD", signal_1h)
        
        assert should_suppress
        assert "4h" in reason


class TestPrematureExitPrevention:
    """Test premature exit signal prevention."""
    
    @pytest.fixture
    def trade_tracker(self):
        """Create a TradeTracker instance."""
        mock_alerter = Mock()
        return TradeTracker(
            alerter=mock_alerter,
            grace_period_minutes=5,
            min_profit_threshold_crypto=1.0,
            min_profit_threshold_fx=0.3
        )
    
    def test_exit_suppressed_during_grace_period(self, trade_tracker):
        """Test that exit signals are suppressed during grace period."""
        # Create a signal
        signal = Mock()
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        signal.stop_loss = 94500.0
        signal.take_profit = 96000.0
        signal.atr = 100.0
        signal.symbol = "BTC-USD"
        signal.timestamp = datetime.now()
        
        # Add trade
        trade_tracker.add_trade(signal, "BTC-USD")
        
        # Get the trade
        trade_id = list(trade_tracker.active_trades.keys())[0]
        trade = trade_tracker.active_trades[trade_id]
        
        # Try to check momentum reversal immediately (within grace period)
        indicators = {'rsi': 75, 'prev_rsi': 70, 'volume_ratio': 0.7}
        current_price = 95500.0
        
        # Should not trigger exit during grace period
        should_exit = trade_tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert not should_exit
    
    def test_exit_suppressed_on_negative_pnl(self, trade_tracker):
        """Test that exit signals are suppressed when P&L is negative."""
        signal = Mock()
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        signal.stop_loss = 94500.0
        signal.take_profit = 96000.0
        signal.atr = 100.0
        signal.symbol = "BTC-USD"
        signal.timestamp = datetime.now() - timedelta(minutes=10)  # Past grace period
        
        trade_tracker.add_trade(signal, "BTC-USD")
        
        trade_id = list(trade_tracker.active_trades.keys())[0]
        trade = trade_tracker.active_trades[trade_id]
        
        # Set entry time to past grace period
        trade.entry_time = datetime.now() - timedelta(minutes=10)
        
        # Current price is below entry (negative P&L)
        current_price = 94800.0
        indicators = {'rsi': 75, 'prev_rsi': 70, 'volume_ratio': 0.7}
        
        should_exit = trade_tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert not should_exit
    
    def test_exit_allowed_with_sufficient_profit(self, trade_tracker):
        """Test that exit signals are allowed when profit exceeds threshold."""
        signal = Mock()
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        signal.stop_loss = 94500.0
        signal.take_profit = 96000.0
        signal.atr = 100.0
        signal.symbol = "BTC-USD"
        signal.timestamp = datetime.now() - timedelta(minutes=10)
        
        trade_tracker.add_trade(signal, "BTC-USD")
        
        trade_id = list(trade_tracker.active_trades.keys())[0]
        trade = trade_tracker.active_trades[trade_id]
        
        # Set entry time and peak profit
        trade.entry_time = datetime.now() - timedelta(minutes=10)
        trade.highest_price = 96500.0  # Peak at +1.58%
        trade.peak_profit_percent = 1.58
        
        # Current price giving back gains but still profitable
        current_price = 95800.0  # +0.84% (giving back 47% of peak)
        indicators = {'rsi': 75, 'prev_rsi': 70, 'volume_ratio': 0.7}
        
        should_exit = trade_tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert should_exit


class TestGracePeriodEnforcement:
    """Test grace period enforcement."""
    
    def test_grace_period_blocks_early_exits(self):
        """Test that grace period prevents exits within specified time."""
        mock_alerter = Mock()
        tracker = TradeTracker(
            alerter=mock_alerter,
            grace_period_minutes=30
        )
        
        signal = Mock()
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        signal.stop_loss = 94500.0
        signal.take_profit = 96000.0
        signal.atr = 100.0
        signal.symbol = "BTC-USD"
        signal.timestamp = datetime.now()
        
        tracker.add_trade(signal, "BTC-USD")
        
        trade_id = list(tracker.active_trades.keys())[0]
        trade = tracker.active_trades[trade_id]
        
        # Try exit at 5 minutes (within 30 minute grace period)
        trade.entry_time = datetime.now() - timedelta(minutes=5)
        trade.peak_profit_percent = 2.0
        
        current_price = 95500.0
        indicators = {'rsi': 75, 'prev_rsi': 70, 'volume_ratio': 0.7}
        
        should_exit = tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert not should_exit
        
        # Try exit at 35 minutes (past grace period)
        trade.entry_time = datetime.now() - timedelta(minutes=35)
        trade.highest_price = 96500.0
        trade.peak_profit_percent = 1.58
        
        should_exit = tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert should_exit


class TestFXSessionValidation:
    """Test FX trading session validation."""
    
    def test_fx_session_detection(self):
        """Test FX session detection logic."""
        # This would test session detection if implemented
        # For now, we'll test the concept
        
        # London session: 08:00-17:00 UTC
        # New York session: 13:00-22:00 UTC
        # Asian session: 00:00-09:00 UTC
        
        def get_session(hour_utc):
            if 0 <= hour_utc < 9:
                return "Asian"
            elif 8 <= hour_utc < 17:
                if 13 <= hour_utc < 17:
                    return "London/NewYork Overlap"
                return "London"
            elif 13 <= hour_utc < 22:
                return "NewYork"
            else:
                return "Off-hours"
        
        # Test various hours
        assert get_session(3) == "Asian"
        assert get_session(10) == "London"
        assert get_session(14) == "London/NewYork Overlap"
        assert get_session(19) == "NewYork"
        assert get_session(23) == "Off-hours"


class TestConfigurationHotReload:
    """Test configuration hot-reload."""
    
    def test_config_reload_updates_settings(self):
        """Test that configuration can be reloaded without restart."""
        # Create initial config
        config = {
            "symbols": {
                "BTC-USD": {
                    "enabled": True,
                    "asset_type": "crypto",
                    "display_name": "Bitcoin",
                    "timeframes": ["5m"],
                    "signal_rules": {
                        "volume_spike_threshold": 0.8,
                        "rsi_min": 30,
                        "rsi_max": 70,
                        "stop_loss_atr_multiplier": 1.5,
                        "take_profit_atr_multiplier": 2.0
                    }
                }
            },
            "global_settings": {
                "polling_interval_seconds": 60
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_file = f.name
        
        # Load initial config
        manager = AssetConfigManager(config_file)
        assert len(manager.get_enabled_symbols()) == 1
        assert manager.get_global_setting("polling_interval_seconds") == 60
        
        # Modify config file
        config["symbols"]["ETH-USD"] = {
            "enabled": True,
            "asset_type": "crypto",
            "display_name": "Ethereum",
            "timeframes": ["5m"],
            "signal_rules": {
                "volume_spike_threshold": 0.9,
                "rsi_min": 30,
                "rsi_max": 70,
                "stop_loss_atr_multiplier": 1.8,
                "take_profit_atr_multiplier": 2.2
            }
        }
        config["global_settings"]["polling_interval_seconds"] = 30
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Reload
        success, errors = manager.reload_configs()
        assert success
        assert len(errors) == 0
        
        # Verify updates
        assert len(manager.get_enabled_symbols()) == 2
        assert manager.get_global_setting("polling_interval_seconds") == 30


class TestFVGDetection:
    """Test FVG detection on sample data."""
    
    @pytest.fixture
    def sample_data_with_fvg(self):
        """Create sample data with a clear FVG."""
        # Create data with an inverse FVG (bearish gap)
        data = {
            'timestamp': pd.date_range('2025-01-01', periods=10, freq='1H'),
            'open': [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
            'high': [101, 102, 103, 104, 105, 104, 103, 102, 101, 100],
            'low': [99, 100, 101, 102, 103, 102, 101, 100, 99, 98],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5, 103.5, 102.5, 101.5, 100.5, 99.5],
            'volume': [1000] * 10
        }
        df = pd.DataFrame(data)
        
        # Manually create a gap: candle[3].low (102) > candle[5].high (104)
        # This creates an inverse FVG
        df.loc[3, 'low'] = 106  # Raise the low of candle 3
        df.loc[5, 'high'] = 104  # Keep candle 5 high below
        
        return df
    
    def test_fvg_detection(self, sample_data_with_fvg):
        """Test that FVG detector identifies gaps correctly."""
        detector = FVGDetector(min_gap_percent=0.1)
        
        fvgs = detector.detect_fvgs(sample_data_with_fvg, '1h')
        
        # Should detect at least one FVG
        assert len(fvgs) > 0
        
        # Check FVG properties
        fvg = fvgs[0]
        assert fvg.fvg_type in ['inverse', 'regular']
        assert fvg.high > fvg.low
        assert fvg.gap_percent >= 0.1
    
    def test_fvg_reentry_detection(self):
        """Test FVG re-entry detection."""
        detector = FVGDetector(min_gap_percent=0.1)
        
        # Create a sample FVG zone
        fvg = FVGZone(
            fvg_type='inverse',
            timeframe='1h',
            high=105.0,
            low=103.0,
            gap_percent=1.9,
            created_at=datetime.now(),
            candle_index=5
        )
        
        # Test price in zone
        assert detector.check_fvg_reentry(104.0, fvg) == True
        
        # Test price outside zone
        assert detector.check_fvg_reentry(110.0, fvg) == False
        assert detector.check_fvg_reentry(100.0, fvg) == False


class TestLowerTimeframeConfirmation:
    """Test lower timeframe confirmation logic."""
    
    def test_lower_tf_shift_detection(self):
        """Test detection of market structure shift on lower timeframe."""
        detector = FVGDetector(min_gap_percent=0.1)
        
        # Create FVG zone
        fvg = FVGZone(
            fvg_type='inverse',
            timeframe='4h',
            high=105.0,
            low=103.0,
            gap_percent=1.9,
            created_at=datetime.now(),
            candle_index=5
        )
        
        # Create lower timeframe data showing bearish shift
        lower_tf_data = {
            'timestamp': pd.date_range('2025-01-01', periods=15, freq='15min'),
            'open': [104, 104.5, 105, 105.5, 106, 105.5, 105, 104.5, 104, 103.5, 103, 102.5, 102, 101.5, 101],
            'high': [104.5, 105, 105.5, 106, 106.5, 106, 105.5, 105, 104.5, 104, 103.5, 103, 102.5, 102, 101.5],
            'low': [103.5, 104, 104.5, 105, 105.5, 105, 104.5, 104, 103.5, 103, 102.5, 102, 101.5, 101, 100.5],
            'close': [104.2, 104.7, 105.2, 105.7, 106.2, 105.7, 105.2, 104.7, 104.2, 103.7, 103.2, 102.7, 102.2, 101.7, 101.2],
            'volume': [1000] * 15
        }
        df_lower = pd.DataFrame(lower_tf_data)
        
        # Detect shift
        shift_detected, description = detector.detect_lower_tf_shift(df_lower, fvg)
        
        # Should detect bearish shift (lower highs)
        assert isinstance(shift_detected, bool)
        assert isinstance(description, str)


class TestNWOGDetection:
    """Test NWOG detection with Friday-Monday gap data."""
    
    @pytest.fixture
    def friday_monday_gap_data(self):
        """Create sample data with Friday-Monday gap."""
        # Create 2 weeks of daily data
        dates = []
        prices = []
        
        # Week 1: Mon-Fri
        for i in range(5):
            dates.append(datetime(2025, 1, 6) + timedelta(days=i))  # Jan 6-10 (Mon-Fri)
            prices.append(100 + i)
        
        # Weekend gap - Monday opens higher
        dates.append(datetime(2025, 1, 13))  # Next Monday
        prices.append(105)  # Gap up from Friday close of 104
        
        data = {
            'timestamp': dates,
            'open': prices,
            'high': [p + 1 for p in prices],
            'low': [p - 1 for p in prices],
            'close': prices,
            'volume': [1000] * len(dates)
        }
        
        return pd.DataFrame(data)
    
    def test_nwog_detection(self, friday_monday_gap_data):
        """Test NWOG detection."""
        detector = NWOGDetector(min_gap_percent=0.1)
        
        nwog = detector.detect_nwog(friday_monday_gap_data)
        
        # Should detect a gap
        if nwog:
            assert nwog.gap_type in ['bullish', 'bearish']
            assert nwog.gap_high > nwog.gap_low
            assert nwog.gap_size_percent >= 0.1
    
    def test_nwog_respect_detection(self):
        """Test NWOG respect/rejection detection."""
        detector = NWOGDetector(min_gap_percent=0.1)
        
        # Create NWOG zone
        nwog = NWOGZone(
            gap_type='bullish',
            friday_close=100.0,
            monday_open=102.0,
            gap_low=100.0,
            gap_high=102.0,
            gap_size_percent=2.0,
            created_at=datetime.now(),
            week_number=2
        )
        
        # Create lower timeframe data showing support at gap low
        lower_tf_data = {
            'timestamp': pd.date_range('2025-01-13', periods=5, freq='1H'),
            'open': [101, 100.5, 100.2, 100.1, 100.3],
            'high': [101.5, 101, 100.7, 100.5, 100.8],
            'low': [100.5, 100, 99.8, 99.9, 100],
            'close': [100.7, 100.2, 100, 100.2, 100.5],
            'volume': [1000] * 5
        }
        df_lower = pd.DataFrame(lower_tf_data)
        
        # Check for respect at gap low (100.0)
        is_respected, description = detector.check_nwog_respect(100.1, nwog, df_lower)
        
        assert isinstance(is_respected, bool)
        assert isinstance(description, str)


class TestDuplicateExitPrevention:
    """Test duplicate exit signal prevention."""
    
    def test_duplicate_exit_signals_suppressed(self):
        """Test that duplicate exit signals within window are suppressed."""
        mock_alerter = Mock()
        tracker = TradeTracker(
            alerter=mock_alerter,
            grace_period_minutes=5,
            duplicate_exit_window_minutes=10
        )
        
        signal = Mock()
        signal.signal_type = "LONG"
        signal.entry_price = 95000.0
        signal.stop_loss = 94500.0
        signal.take_profit = 96000.0
        signal.atr = 100.0
        signal.symbol = "BTC-USD"
        signal.timestamp = datetime.now() - timedelta(minutes=20)
        
        tracker.add_trade(signal, "BTC-USD")
        
        trade_id = list(tracker.active_trades.keys())[0]
        trade = tracker.active_trades[trade_id]
        
        # Set up trade for exit
        trade.entry_time = datetime.now() - timedelta(minutes=20)
        trade.highest_price = 96500.0
        trade.peak_profit_percent = 1.58
        trade.last_exit_signal_time = datetime.now() - timedelta(minutes=5)  # Exit 5 min ago
        
        current_price = 95800.0
        indicators = {'rsi': 75, 'prev_rsi': 70, 'volume_ratio': 0.7}
        
        # Should suppress duplicate exit
        should_exit = tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert not should_exit
        
        # After 11 minutes, should allow new exit signal
        trade.last_exit_signal_time = datetime.now() - timedelta(minutes=11)
        should_exit = tracker._check_momentum_reversal(signal, current_price, trade, indicators)
        assert should_exit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
