"""
Consolidated imports for the scanner system.
Provides a single location for importing all core modules and utilities.
"""

# Core utilities
from src.scanner_utils import (
    setup_logging,
    load_json_config,
    create_signal_handler,
    register_signal_handlers
)

# Configuration
from src.config_loader import ConfigLoader
from src.config_validator import ConfigValidator
from src.asset_config_manager import AssetConfigManager

# Data sources
from src.unified_data_source import UnifiedDataSource
from src.market_data_client import MarketDataClient
from src.yfinance_client import YFinanceClient
from src.hybrid_data_client import HybridDataClient

# Indicators
from src.indicator_calculator import IndicatorCalculator

# Strategies
from src.strategies import (
    FibonacciRetracement,
    H4HVG,
    SupportResistance,
    EMACrossover,
    MomentumShift,
    TrendAlignment,
    MeanReversion
)

# Signal detection
from src.signal_detector import SignalDetector, Signal
from src.signal_quality_filter import SignalQualityFilter, QualityConfig
from src.strategy_detector import StrategyDetector

# Alerting and reporting
from src.alerter import EmailAlerter, TelegramAlerter, MultiAlerter
from src.excel_reporter import ExcelReporter
from src.trade_tracker import TradeTracker

# Monitoring and diagnostics
from src.health_monitor import HealthMonitor, setup_logging as setup_logging_health
from src.signal_diagnostics import SignalDiagnostics

# Scanners
from src.base_scanner import BaseScanner
from src.scanners import (
    BTCScalpScanner,
    BTCSwingScanner,
    GoldScalpScanner,
    GoldSwingScanner,
    US30ScalpScanner,
    US30SwingScanner,
    US100Scanner,
    MultiCryptoScanner
)

# Orchestration
from src.scanner_orchestrator import ScannerOrchestrator
from src.symbol_orchestrator import SymbolOrchestrator

__all__ = [
    # Utilities
    'setup_logging',
    'load_json_config',
    'create_signal_handler',
    'register_signal_handlers',
    
    # Configuration
    'ConfigLoader',
    'ConfigValidator',
    'AssetConfigManager',
    
    # Data sources
    'UnifiedDataSource',
    'MarketDataClient',
    'YFinanceClient',
    'HybridDataClient',
    
    # Indicators
    'IndicatorCalculator',
    
    # Strategies
    'FibonacciRetracement',
    'H4HVG',
    'SupportResistance',
    'EMACrossover',
    'MomentumShift',
    'TrendAlignment',
    'MeanReversion',
    
    # Signal detection
    'SignalDetector',
    'Signal',
    'SignalQualityFilter',
    'QualityConfig',
    'StrategyDetector',
    
    # Alerting and reporting
    'EmailAlerter',
    'TelegramAlerter',
    'MultiAlerter',
    'ExcelReporter',
    'TradeTracker',
    
    # Monitoring
    'HealthMonitor',
    'SignalDiagnostics',
    
    # Scanners
    'BaseScanner',
    'BTCScalpScanner',
    'BTCSwingScanner',
    'GoldScalpScanner',
    'GoldSwingScanner',
    'US30ScalpScanner',
    'US30SwingScanner',
    'US100Scanner',
    'MultiCryptoScanner',
    
    # Orchestration
    'ScannerOrchestrator',
    'SymbolOrchestrator'
]
