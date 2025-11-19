# Scanner System - Core Modules

This directory contains all core modules for the unified trading scanner system.

## Directory Structure

### Core Utilities
- `scanner_utils.py` - Shared utility functions (logging, config loading, signal handlers)
- `imports.py` - Consolidated imports for easy access to all modules

### Configuration Management
- `config_loader.py` - Load and parse configuration files
- `config_validator.py` - Validate configuration parameters
- `config_manager.py` - Manage configuration state
- `asset_config_manager.py` - Asset-specific configuration management

### Data Sources
- `unified_data_source.py` - Unified data client with automatic fallback
- `market_data_client.py` - Generic market data client
- `yfinance_client.py` - Yahoo Finance data provider
- `hybrid_data_client.py` - Multi-provider hybrid data client
- `alpha_vantage_client.py` - Alpha Vantage API client
- `twelve_data_client.py` - Twelve Data API client
- `mt5_data_client.py` - MetaTrader 5 data client
- `websocket_streamer.py` - WebSocket streaming for real-time data

### Indicators
- `indicator_calculator.py` - Calculate all technical indicators (EMA, RSI, ATR, etc.)
- `market_data_models.py` - Data models for market data

### Strategies
- `strategies/` - Consolidated strategy implementations
  - `fibonacci_retracement.py` - Fibonacci retracement strategy
  - `h4_hvg.py` - 4-hour higher volume gap strategy
  - `support_resistance.py` - Support/resistance bounce strategy
  - `ema_crossover.py` - EMA crossover strategy
  - `momentum_shift.py` - Momentum shift strategy
  - `trend_alignment.py` - Trend alignment strategy
  - `mean_reversion.py` - Mean reversion strategy

### Signal Detection
- `signal_detector.py` - Main signal detection engine
- `signal_detector_clean.py` - Alternative signal detector implementation
- `signal_quality_filter.py` - Filter signals by confluence factors
- `strategy_detector.py` - Coordinate multiple strategies
- `strategy_registry.py` - Registry for strategy management
- `strategy_orchestrator.py` - Orchestrate strategy selection
- `strategy_helpers.py` - Strategy helper utilities
- `future_signal_detector.py` - Detect future signals (predictive)

### Advanced Detection
- `fvg_detector.py` - Fair Value Gap detection
- `h4_hvg_detector.py` - 4-hour HVG detection
- `nwog_detector.py` - New Week Opening Gap detection
- `fibonacci_strategy.py` - Fibonacci strategy (legacy, use strategies/fibonacci_retracement.py)
- `support_resistance_strategy.py` - Support/Resistance strategy (legacy)
- `us30_strategy.py` - US30-specific strategy

### Alerting & Reporting
- `alerter.py` - Email and Telegram alerting
- `excel_reporter.py` - Excel reporting and logging
- `trade_tracker.py` - Track open trades and manage TP/SL

### Monitoring & Diagnostics
- `health_monitor.py` - System health monitoring
- `signal_diagnostics.py` - Signal detection diagnostics
- `data_validation.py` - Data validation utilities
- `price_validator.py` - Price validation

### Scanners
- `base_scanner.py` - Base class for all scanners
- `scanners/` - Unified scanner implementations
  - `btc_scalp_scanner.py` - BTC scalping scanner
  - `btc_swing_scanner.py` - BTC swing trading scanner
  - `gold_scalp_scanner.py` - Gold scalping scanner
  - `gold_swing_scanner.py` - Gold swing trading scanner
  - `us30_scalp_scanner.py` - US30 scalping scanner
  - `us30_swing_scanner.py` - US30 swing trading scanner
  - `us100_scanner.py` - US100/NASDAQ scanner
  - `multi_crypto_scanner.py` - Multi-symbol crypto scanner

### Orchestration
- `scanner_orchestrator.py` - Manage all 8 scanners
- `symbol_orchestrator.py` - Manage multi-symbol scanning
- `symbol_scanner.py` - Individual symbol scanner
- `symbol_context.py` - Symbol-specific context

### Utilities
- `liquidity_filter.py` - Liquidity filtering
- `bypass_mode.py` - Bypass mode for testing
- `news_calendar.py` - News event calendar
- `market_structure.py` - Market structure analysis
- `trend_analyzer.py` - Trend analysis utilities
- `sl_tp_calculator.py` - Stop-loss and take-profit calculation

## Usage

### Importing Modules

Use the consolidated imports module for easy access:

```python
from src.imports import (
    setup_logging,
    ConfigLoader,
    BTCScalpScanner,
    ScannerOrchestrator
)
```

Or import specific modules directly:

```python
from src.scanner_utils import setup_logging, load_json_config
from src.scanners import BTCScalpScanner
```

### Creating a Scanner

```python
from src.scanners import BTCScalpScanner

scanner = BTCScalpScanner(config_path="config/config.json")
scanner.start()
```

### Running All Scanners

```python
from src.scanner_orchestrator import ScannerOrchestrator

orchestrator = ScannerOrchestrator(config_path="config/config.json")
orchestrator.start_all_scanners()
```

## Code Organization Principles

1. **Unified Architecture** - All scanners inherit from `BaseScanner`
2. **Pluggable Strategies** - Strategies in `strategies/` directory are easily swappable
3. **Consolidated Utilities** - Common functions in `scanner_utils.py`
4. **Centralized Imports** - Use `imports.py` for easy module access
5. **Clear Separation** - Core logic, strategies, and scanners are clearly separated

## Migration Notes

- Old scanner-specific code in `us30_scanner/` and `xauusd_scanner/` directories has been consolidated
- Legacy strategy files (e.g., `fibonacci_strategy.py`) are maintained for backward compatibility
- New code should use the unified implementations in `strategies/` directory
- Main entry points should use utilities from `scanner_utils.py`
