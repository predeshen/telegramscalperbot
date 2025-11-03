# Design Document

## Overview

This design adds trend-following capabilities to all three scanners (BTC, US30, XAUUSD) and enhances Excel reporting to capture complete scan data. The implementation will:

1. Add a `_detect_trend_following()` method to both `SignalDetector` (BTC/US30) and `GoldSignalDetector` (XAUUSD)
2. Implement swing point detection to identify higher highs/lows and lower highs/lows
3. Add TREND_FOLLOWING strategy to XAUUSD's StrategySelector
4. Enhance ExcelReporter to log all indicators, signal details, and strategy-specific metadata
5. Ensure consistent Excel file structure across all scanners

## Architecture

### Component Interaction

```
┌─────────────────┐
│  Scanner Main   │
│  (BTC/US30/     │
│   XAUUSD)       │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
         v                  v
┌────────────────┐   ┌──────────────┐
│ SignalDetector │   │ExcelReporter │
│ (or Gold       │   │              │
│  SignalDetector│   │              │
└────────┬───────┘   └──────┬───────┘
         │                  │
         v                  v
┌────────────────┐   ┌──────────────┐
│ Trend Following│   │ Excel File   │
│ Detection      │   │ (.xlsx)      │
│ Logic          │   │              │
└────────────────┘   └──────────────┘
```

### Data Flow

1. Scanner fetches market data and calculates indicators
2. SignalDetector analyzes data for trend patterns
3. If trend detected, generate signal with full metadata
4. ExcelReporter logs scan result with all data fields
5. Periodic email reports sent with Excel attachment

## Components and Interfaces

### 1. Trend Detection Module

#### TrendAnalyzer Class (New)

A helper class to identify trend patterns:

```python
class TrendAnalyzer:
    """Analyzes price data to identify trends."""
    
    @staticmethod
    def detect_swing_points(data: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Detect swing highs and swing lows.
        
        Returns:
            {
                'swing_highs': [(index, price), ...],
                'swing_lows': [(index, price), ...],
                'higher_highs': int,  # Count of higher highs
                'higher_lows': int,   # Count of higher lows
                'lower_highs': int,   # Count of lower highs
                'lower_lows': int     # Count of lower lows
            }
        """
    
    @staticmethod
    def is_uptrend(swing_data: Dict, min_swings: int = 3) -> bool:
        """Check if data shows uptrend pattern."""
    
    @staticmethod
    def is_downtrend(swing_data: Dict, min_swings: int = 3) -> bool:
        """Check if data shows downtrend pattern."""
    
    @staticmethod
    def calculate_pullback_depth(data: pd.DataFrame, trend_direction: str) -> float:
        """Calculate pullback depth as percentage of previous trend leg."""
    
    @staticmethod
    def is_ema_aligned(data: pd.DataFrame, trend_direction: str) -> bool:
        """Check if EMAs are aligned with trend direction."""
```

### 2. Enhanced SignalDetector (BTC/US30)

Add trend-following detection to existing `SignalDetector` class:

```python
class SignalDetector:
    """Existing class with new trend-following method."""
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
        """
        Enhanced to check for trend-following signals.
        
        Detection order:
        1. Check existing strategies (volume spike, EMA crossover, etc.)
        2. If no signal, check for trend-following opportunity
        """
    
    def _detect_trend_following(self, data: pd.DataFrame, timeframe: str) -> Optional[Signal]:
        """
        Detect trend-following signals.
        
        Logic:
        1. Use TrendAnalyzer to detect swing points
        2. Verify trend with EMA alignment
        3. Check for pullback to EMA(21)
        4. Confirm bounce with volume
        5. Validate RSI range
        6. Generate signal with proper risk management
        
        Returns:
            Signal with strategy="Trend Following"
        """
```

### 3. Enhanced GoldSignalDetector (XAUUSD)

Add trend-following as fourth strategy:

```python
class GoldSignalDetector:
    """Existing class with new trend-following method."""
    
    def detect_signals(self, data: pd.DataFrame, timeframe: str) -> Optional[GoldSignal]:
        """
        Enhanced to route to trend-following strategy.
        
        Strategy selection now includes:
        1. ASIAN_RANGE_BREAKOUT
        2. EMA_CLOUD_BREAKOUT
        3. MEAN_REVERSION
        4. TREND_FOLLOWING (new)
        """
    
    def _detect_trend_following(self, data: pd.DataFrame, timeframe: str) -> Optional[GoldSignal]:
        """
        Detect trend-following signals for Gold.
        
        Similar to SignalDetector but with Gold-specific enhancements:
        - Session awareness (prefer London/NY for trends)
        - Key level integration
        - Spread monitoring
        - Asian range context
        """
```

### 4. Enhanced StrategySelector (XAUUSD)

Add TREND_FOLLOWING strategy:

```python
class GoldStrategy(Enum):
    """Existing enum with new strategy."""
    ASIAN_RANGE_BREAKOUT = "Asian Range Breakout"
    EMA_CLOUD_BREAKOUT = "EMA Cloud Breakout"
    MEAN_REVERSION = "Mean Reversion"
    TREND_FOLLOWING = "Trend Following"  # New
    NO_TRADE = "No Trade"

class StrategySelector:
    """Existing class with enhanced selection logic."""
    
    def select_strategy(self, data: pd.DataFrame, session: TradingSession) -> GoldStrategy:
        """
        Enhanced to select TREND_FOLLOWING when appropriate.
        
        Selection logic:
        1. If strong trend detected (3+ swing points, EMA aligned)
           -> TREND_FOLLOWING
        2. If London session and Asian range finalized
           -> ASIAN_RANGE_BREAKOUT
        3. If trending market with breakout
           -> EMA_CLOUD_BREAKOUT
        4. If overextended from VWAP
           -> MEAN_REVERSION
        5. Otherwise
           -> NO_TRADE
        """
```

### 5. Enhanced ExcelReporter

Expand data logging capabilities:

```python
class ExcelReporter:
    """Existing class with enhanced logging."""
    
    def log_scan_result(self, scan_data: Dict) -> None:
        """
        Enhanced to log complete scan data.
        
        New fields logged:
        - All indicator values (EMA 9/21/50/100/200, RSI, ATR, VWAP, Volume MA)
        - Complete signal details (entry, stop, target, R:R, strategy, confidence)
        - XAUUSD-specific: session, spread, Asian range
        - Trend-specific: swing points, pullback depth, trend direction
        """
    
    def _get_excel_columns(self) -> List[str]:
        """
        Define complete column structure.
        
        Returns:
            [
                'Timestamp', 'Scanner', 'Symbol', 'Timeframe',
                'Price', 'Volume',
                'EMA_9', 'EMA_21', 'EMA_50', 'EMA_100', 'EMA_200',
                'RSI', 'ATR', 'VWAP', 'Volume_MA',
                'Signal_Detected', 'Signal_Type', 'Entry_Price',
                'Stop_Loss', 'Take_Profit', 'Risk_Reward',
                'Strategy', 'Confidence', 'Market_Bias',
                'Session', 'Spread_Pips',  # XAUUSD only
                'Trend_Direction', 'Swing_Points', 'Pullback_Depth'  # Trend signals
            ]
        """
    
    def _format_scan_row(self, scan_data: Dict) -> Dict:
        """
        Format scan data into Excel row.
        
        Handles:
        - Missing values (write "N/A")
        - Numeric formatting (2 decimals for prices, 1 for percentages)
        - Nested dictionaries (flatten signal_details, indicators)
        - Scanner-specific fields (XAUUSD session data)
        """
```

## Data Models

### Enhanced Signal Data Structure

```python
@dataclass
class Signal:
    """Enhanced with trend-following metadata."""
    # Existing fields
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    risk_reward: float
    market_bias: str
    confidence: int
    indicators: Dict
    reasoning: str
    
    # New fields for trend-following
    strategy: str = ""  # "Trend Following", "EMA Cloud Breakout", etc.
    trend_direction: Optional[str] = None  # "uptrend" or "downtrend"
    swing_points: Optional[int] = None  # Number of swing highs/lows
    pullback_depth: Optional[float] = None  # Percentage pullback
```

### Excel Scan Data Structure

```python
{
    'timestamp': datetime,
    'scanner': str,  # "BTC-Swing", "US30-Swing", "XAUUSD-Swing-London"
    'symbol': str,
    'timeframe': str,
    'price': float,
    'volume': float,
    'indicators': {
        'ema_9': float,
        'ema_21': float,
        'ema_50': float,
        'ema_100': float,  # BTC/US30 only
        'ema_200': float,  # BTC/US30 only
        'rsi': float,
        'atr': float,
        'vwap': float,
        'volume_ma': float
    },
    'signal_detected': bool,
    'signal_type': Optional[str],  # "LONG", "SHORT", or None
    'signal_details': {
        'entry_price': float,
        'stop_loss': float,
        'take_profit': float,
        'risk_reward': float,
        'strategy': str,
        'confidence': int,
        'market_bias': str,
        'trend_direction': Optional[str],
        'swing_points': Optional[int],
        'pullback_depth': Optional[float]
    },
    'xauusd_specific': {  # Only for XAUUSD scanner
        'session': str,
        'spread_pips': float,
        'asian_range_high': Optional[float],
        'asian_range_low': Optional[float]
    }
}
```

## Error Handling

### Trend Detection Errors

1. **Insufficient Data**: If less than 50 candles available, skip trend detection
2. **Invalid Swing Points**: If swing point detection fails, log warning and return None
3. **EMA Calculation Errors**: If EMAs not available, skip EMA alignment check
4. **Division by Zero**: Handle cases where ATR or price range is zero

### Excel Logging Errors

1. **Missing Indicators**: Write "N/A" for missing indicator values
2. **File Write Errors**: Log error and retry once, then skip if still failing
3. **Invalid Data Types**: Convert to string representation if type mismatch
4. **Column Mismatch**: Dynamically add missing columns if structure changes

## Testing Strategy

### Unit Tests

1. **TrendAnalyzer Tests**
   - Test swing point detection with known patterns
   - Test uptrend/downtrend identification
   - Test pullback depth calculation
   - Test EMA alignment verification

2. **SignalDetector Tests**
   - Test trend-following signal generation
   - Test signal filtering (RSI, volume, pullback depth)
   - Test risk management calculations
   - Test duplicate detection

3. **ExcelReporter Tests**
   - Test complete data logging
   - Test column structure
   - Test data formatting
   - Test missing value handling

### Integration Tests

1. **End-to-End Scanner Tests**
   - Run each scanner with trend-following enabled
   - Verify signals generated for known trending markets
   - Verify Excel files contain all expected columns
   - Verify email reports sent successfully

2. **Multi-Scanner Tests**
   - Run all three scanners simultaneously
   - Verify no conflicts or data corruption
   - Verify each scanner logs to correct Excel file
   - Verify trend detection works independently per scanner

### Manual Testing

1. **Historical Data Testing**
   - Test with historical trending markets (e.g., Gold uptrend in chart)
   - Verify signals would have been generated
   - Verify signal quality and timing

2. **Excel File Validation**
   - Open generated Excel files
   - Verify all columns present
   - Verify data formatting correct
   - Verify no missing or corrupted data

## Implementation Notes

### Performance Considerations

1. **Swing Point Detection**: Use vectorized pandas operations for efficiency
2. **Caching**: Cache swing point analysis for 5 minutes to avoid recalculation
3. **Excel Writing**: Use openpyxl's write-only mode for large datasets
4. **Memory Management**: Limit Excel file to last 10,000 rows, archive older data

### Configuration

Add to scanner configs:

```json
{
  "signal_detection": {
    "trend_following": {
      "enabled": true,
      "min_swing_points": 3,
      "max_pullback_percent": 50,
      "min_volume_ratio": 1.2,
      "rsi_range_uptrend": [40, 80],
      "rsi_range_downtrend": [20, 60]
    }
  },
  "excel_reporting": {
    "log_all_indicators": true,
    "log_trend_metadata": true,
    "max_rows": 10000
  }
}
```

### Backward Compatibility

1. Existing signal detection methods remain unchanged
2. Trend-following is additive, not replacing existing strategies
3. Excel files will have new columns, but existing columns unchanged
4. Old Excel files can still be read (missing columns will be added)

## Deployment Considerations

### Rollout Plan

1. **Phase 1**: Deploy TrendAnalyzer and unit tests
2. **Phase 2**: Add trend-following to BTC scanner, test for 24 hours
3. **Phase 3**: Add trend-following to US30 scanner, test for 24 hours
4. **Phase 4**: Add trend-following to XAUUSD scanner, test for 24 hours
5. **Phase 5**: Deploy enhanced Excel logging to all scanners
6. **Phase 6**: Monitor for 1 week, adjust parameters if needed

### Monitoring

1. Log trend-following signal count per scanner
2. Monitor Excel file sizes and write performance
3. Track email delivery success rate
4. Monitor false signal rate (signals that immediately hit stop-loss)

### Rollback Plan

If issues arise:
1. Disable trend-following via config (`"enabled": false`)
2. Revert to previous SignalDetector version
3. Excel logging will continue with existing fields
4. No data loss, only feature disabled
