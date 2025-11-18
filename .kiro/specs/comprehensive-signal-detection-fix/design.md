# Design Document

## Overview

This design addresses systematic signal detection failures across 8 trading scanners by implementing relaxed thresholds, enhanced diagnostics, and per-scanner customization. The solution focuses on three core areas: (1) threshold calibration to match real market conditions, (2) diagnostic tooling to identify suppression causes, and (3) configuration flexibility for asset-specific tuning.

## Architecture

### Component Hierarchy

```
Scanner Application (main.py, main_swing.py, main_us30.py, main_multi_symbol.py)
    ├── Configuration Layer (config_loader.py, asset_config_manager.py)
    │   ├── Global Defaults
    │   ├── Asset-Specific Overrides
    │   └── Validation & Logging
    │
    ├── Data Layer (market_data_client.py, yfinance_client.py, hybrid_data_client.py)
    │   ├── Data Freshness Validation
    │   ├── Indicator Calculation (indicator_calculator.py)
    │   └── Data Quality Metrics
    │
    ├── Detection Layer (signal_detector.py)
    │   ├── Strategy Detectors (EMA Crossover, Mean Reversion, Trend Alignment, etc.)
    │   ├── Detection Attempt Logging
    │   └── Threshold Application
    │
    ├── Filtering Layer (signal_quality_filter.py, signal_filter.py)
    │   ├── Confluence Evaluation
    │   ├── Confidence Scoring
    │   ├── Duplicate Detection
    │   └── Filter Rejection Logging
    │
    ├── Diagnostic System (NEW: signal_diagnostics.py)
    │   ├── Configuration Analyzer
    │   ├── Detection Rate Tracker
    │   ├── Filter Impact Analyzer
    │   └── Report Generator
    │
    └── Alerting Layer (alerter.py)
        ├── Telegram Alerts
        ├── Email Alerts
        └── Diagnostic Notifications
```

### Data Flow

```
Market Data → Indicator Calculation → Strategy Detection → Quality Filter → Duplicate Check → Alert
                                            ↓                      ↓              ↓
                                    Detection Logger      Filter Logger   Suppression Logger
                                            ↓                      ↓              ↓
                                            └──────────────────────┴──────────────┘
                                                                   ↓
                                                        Diagnostic Analyzer
                                                                   ↓
                                                        Daily Summary Report
```

## Components and Interfaces

### 1. Configuration System Enhancements

#### 1.1 Threshold Configuration Structure

```python
# Global defaults (config/config.json)
{
  "signal_rules": {
    "volume_spike_threshold": 1.3,  # Reduced from 1.5
    "rsi_min": 25,  # Expanded from 30
    "rsi_max": 75,  # Expanded from 70
    "adx_min_trend_alignment": 15,  # Reduced from 19
    "adx_min_momentum_shift": 15,  # Reduced from 20
    "duplicate_time_window_minutes": 10,  # Increased from 5
    "duplicate_price_threshold_percent": 1.0  # Increased from 0.5
  },
  
  "quality_filter": {
    "min_confluence_factors": 3,  # Reduced from 4
    "min_confidence_score": 3,  # Reduced from 4
    "min_risk_reward": 1.2,  # Reduced from 1.5
    "duplicate_window_seconds": 600  # 10 minutes
  },
  
  "asset_specific": {
    "BTC": {
      "volume_thresholds": {
        "scalp": 1.3,
        "swing": 1.2,
        "trend_alignment": 0.8,
        "breakout": 1.3,
        "mean_reversion": 1.5
      },
      "rsi_range": {
        "min": 25,
        "max": 75
      },
      "adx_minimum": 15
    },
    "XAUUSD": {
      "volume_thresholds": {
        "scalp": 1.4,
        "swing": 1.3,
        "trend_alignment": 0.9,
        "breakout": 1.4,
        "mean_reversion": 1.6
      },
      "rsi_range": {
        "min": 25,
        "max": 75
      },
      "adx_minimum": 15
    },
    "US30": {
      "volume_thresholds": {
        "momentum": 1.5,
        "trend_alignment": 1.0,
        "breakout": 1.5
      },
      "rsi_range": {
        "min": 30,
        "max": 70
      },
      "adx_minimum": 20
    }
  },
  
  "diagnostics": {
    "enabled": true,
    "log_detection_attempts": true,
    "log_filter_rejections": true,
    "daily_summary_time": "18:00",
    "alert_on_no_signals_hours": 4
  },
  
  "bypass_mode": {
    "enabled": false,
    "auto_disable_after_hours": 2
  }
}
```

#### 1.2 Configuration Validation

```python
class ConfigValidator:
    """Validates configuration parameters and logs warnings"""
    
    REASONABLE_BOUNDS = {
        'volume_spike_threshold': (0.5, 3.0),
        'rsi_min': (10, 40),
        'rsi_max': (60, 90),
        'adx_min': (10, 30),
        'min_risk_reward': (0.8, 3.0),
        'min_confluence_factors': (2, 5),
        'min_confidence_score': (2, 5)
    }
    
    def validate_config(self, config: dict) -> List[str]:
        """
        Validate configuration and return list of warnings
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check each parameter against reasonable bounds
        for param, (min_val, max_val) in self.REASONABLE_BOUNDS.items():
            value = self._get_nested_value(config, param)
            if value is not None:
                if value < min_val or value > max_val:
                    warnings.append(
                        f"{param}={value} is outside reasonable range "
                        f"[{min_val}, {max_val}]. Recommended: {(min_val + max_val) / 2}"
                    )
        
        return warnings
```

### 2. Diagnostic System (NEW)

#### 2.1 SignalDiagnostics Class

```python
class SignalDiagnostics:
    """
    Comprehensive diagnostic system for signal detection analysis
    """
    
    def __init__(self, scanner_name: str):
        self.scanner_name = scanner_name
        self.detection_attempts = defaultdict(int)  # strategy -> count
        self.successful_detections = defaultdict(int)  # strategy -> count
        self.filter_rejections = defaultdict(int)  # reason -> count
        self.data_quality_issues = defaultdict(int)  # issue_type -> count
        self.last_signal_time = None
        self.start_time = datetime.now()
    
    def log_detection_attempt(self, strategy: str, success: bool, reason: str = ""):
        """Log a strategy detection attempt"""
        self.detection_attempts[strategy] += 1
        if success:
            self.successful_detections[strategy] += 1
        else:
            self.filter_rejections[reason] += 1
    
    def log_data_quality_issue(self, issue_type: str):
        """Log a data quality problem"""
        self.data_quality_issues[issue_type] += 1
    
    def generate_report(self) -> str:
        """Generate diagnostic report"""
        runtime = datetime.now() - self.start_time
        
        report = f"""
=== Signal Detection Diagnostic Report ===
Scanner: {self.scanner_name}
Runtime: {runtime}
Last Signal: {self.last_signal_time or 'Never'}

Detection Attempts by Strategy:
"""
        for strategy, count in self.detection_attempts.items():
            success_count = self.successful_detections.get(strategy, 0)
            success_rate = (success_count / count * 100) if count > 0 else 0
            report += f"  {strategy}: {count} attempts, {success_count} successful ({success_rate:.1f}%)\n"
        
        report += "\nFilter Rejections:\n"
        for reason, count in sorted(self.filter_rejections.items(), key=lambda x: x[1], reverse=True):
            report += f"  {reason}: {count}\n"
        
        if self.data_quality_issues:
            report += "\nData Quality Issues:\n"
            for issue, count in self.data_quality_issues.items():
                report += f"  {issue}: {count}\n"
        
        return report
    
    def get_recommendations(self) -> List[str]:
        """Generate recommendations based on diagnostic data"""
        recommendations = []
        
        # Check for low detection rates
        for strategy, attempts in self.detection_attempts.items():
            if attempts > 10:
                success_rate = self.successful_detections.get(strategy, 0) / attempts
                if success_rate < 0.05:  # Less than 5% success
                    recommendations.append(
                        f"⚠️ {strategy} has very low success rate ({success_rate*100:.1f}%). "
                        f"Consider relaxing thresholds."
                    )
        
        # Check for dominant rejection reasons
        total_rejections = sum(self.filter_rejections.values())
        if total_rejections > 0:
            for reason, count in self.filter_rejections.items():
                if count / total_rejections > 0.5:  # More than 50% of rejections
                    recommendations.append(
                        f"⚠️ {reason} is blocking {count/total_rejections*100:.0f}% of signals. "
                        f"Review this filter threshold."
                    )
        
        # Check for no signals
        if self.last_signal_time is None and (datetime.now() - self.start_time).total_seconds() > 3600:
            recommendations.append(
                "🚨 No signals generated in over 1 hour. Consider enabling bypass mode for testing."
            )
        
        return recommendations
```

#### 2.2 Detection Attempt Logging

```python
# In SignalDetector class
def detect_signals(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
    """Enhanced with diagnostic logging"""
    
    # Try each strategy and log attempts
    strategies = [
        ('EMA Crossover', self._detect_ema_crossover),
        ('Trend Alignment', self._detect_trend_alignment),
        ('Mean Reversion', self._detect_mean_reversion),
        ('EMA Cloud Breakout', self._detect_ema_cloud_breakout),
        ('Momentum Shift', self._detect_momentum_shift)
    ]
    
    for strategy_name, strategy_func in strategies:
        try:
            signal = strategy_func(data, timeframe, symbol)
            
            if signal:
                logger.info(f"✓ {strategy_name} detected signal: {signal.signal_type}")
                if self.diagnostics:
                    self.diagnostics.log_detection_attempt(strategy_name, True)
                return signal
            else:
                logger.debug(f"✗ {strategy_name} no signal")
                if self.diagnostics:
                    self.diagnostics.log_detection_attempt(strategy_name, False, "Pattern not met")
        
        except Exception as e:
            logger.error(f"Error in {strategy_name}: {e}")
            if self.diagnostics:
                self.diagnostics.log_detection_attempt(strategy_name, False, f"Error: {str(e)}")
    
    return None
```

### 3. Quality Filter Enhancements

#### 3.1 Relaxed Thresholds

```python
@dataclass
class QualityConfig:
    """Updated configuration with relaxed thresholds"""
    min_confluence_factors: int = 3  # Changed from 4
    min_confidence_score: int = 3  # Changed from 4
    duplicate_window_seconds: int = 600  # Changed from 300 (10 minutes)
    duplicate_price_tolerance_pct: float = 1.0  # Changed from 0.5
    significant_price_move_pct: float = 1.5  # Changed from 1.0
    min_risk_reward: float = 1.2  # Changed from 1.5
```

#### 3.2 Enhanced Rejection Logging

```python
def evaluate_signal(self, signal: Signal, market_data: Optional[pd.DataFrame] = None) -> FilterResult:
    """Enhanced with detailed rejection logging"""
    
    # Calculate confluence
    confluence_dict = self.calculate_confluence_factors(signal, market_data)
    confluence_factors = [k for k, v in confluence_dict.items() if v]
    confidence_score = self.calculate_confidence_score(confluence_dict)
    
    # Check confluence threshold
    if len(confluence_factors) < self.config.min_confluence_factors:
        missing = [k for k, v in confluence_dict.items() if not v]
        reason = f"Insufficient confluence: {len(confluence_factors)}/{self.config.min_confluence_factors} (missing: {', '.join(missing)})"
        
        logger.info(f"❌ Signal rejected: {reason}")
        logger.info(f"   Factors met: {', '.join(confluence_factors)}")
        logger.info(f"   Factors missing: {', '.join(missing)}")
        
        if self.diagnostics:
            self.diagnostics.log_detection_attempt("Quality Filter", False, reason)
        
        return FilterResult(passed=False, confidence_score=confidence_score, 
                          confluence_factors=confluence_factors, rejection_reason=reason)
    
    # Similar detailed logging for other checks...
```

### 4. Strategy Detection Improvements

#### 4.1 EMA Crossover Strategy

```python
def _detect_ema_crossover(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
    """
    Simplified EMA crossover detection
    
    Changes:
    - Removed EMA50 cascade requirement
    - Reduced volume threshold to 1.3x (from 1.5x)
    - Expanded RSI range to 25-75 (from 30-70)
    """
    
    # Check EMA9 vs EMA21 only (removed EMA50 requirement)
    bullish_cross = last['ema_9'] > last['ema_21'] and prev['ema_9'] <= prev['ema_21']
    bearish_cross = last['ema_9'] < last['ema_21'] and prev['ema_9'] >= prev['ema_21']
    
    # Relaxed volume threshold
    volume_threshold = asset_config.get('volume_thresholds', {}).get('scalp', 1.3)
    volume_ratio = last['volume'] / last['volume_ma']
    
    if volume_ratio < volume_threshold:
        logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x < {volume_threshold}x")
        return None
    
    # Expanded RSI range
    rsi_min = asset_config.get('rsi_range', {}).get('min', 25)
    rsi_max = asset_config.get('rsi_range', {}).get('max', 75)
    
    if last['rsi'] < rsi_min or last['rsi'] > rsi_max:
        logger.debug(f"[{timeframe}] RSI out of range: {last['rsi']:.1f} (need {rsi_min}-{rsi_max})")
        return None
    
    # Rest of logic...
```

#### 4.2 Trend Alignment Strategy

```python
def _detect_trend_alignment(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
    """
    Relaxed trend alignment detection
    
    Changes:
    - Reduced ADX minimum from 19 to 15
    - Reduced volume threshold to 0.8x (from 1.0x)
    - Removed strict EMA cascade requirement
    """
    
    # Get asset-specific ADX minimum
    adx_min = asset_config.get('adx_minimum', 15)
    
    if last['adx'] < adx_min:
        logger.debug(f"[{timeframe}] ADX too low: {last['adx']:.1f} < {adx_min}")
        return None
    
    # Relaxed volume threshold for trend following
    volume_threshold = asset_config.get('volume_thresholds', {}).get('trend_alignment', 0.8)
    volume_ratio = last['volume'] / last['volume_ma']
    
    if volume_ratio < volume_threshold:
        logger.debug(f"[{timeframe}] Volume too low: {volume_ratio:.2f}x < {volume_threshold}x")
        return None
    
    # Rest of logic...
```

#### 4.3 Mean Reversion Strategy

```python
def _detect_mean_reversion(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:
    """
    Adjusted mean reversion detection
    
    Changes:
    - Reduced overextension from 1.8 ATR to 1.5 ATR
    - Reduced volume threshold to 1.5x (from 1.8x)
    - Expanded RSI extremes to <20 or >80 (from <25 or >75)
    """
    
    # Check overextension (1.5 ATR from VWAP)
    distance_from_vwap = abs(current_price - vwap)
    
    if distance_from_vwap < (atr * 1.5):  # Changed from 1.8
        logger.debug(f"[{timeframe}] Price not overextended: {distance_from_vwap:.2f} < {atr * 1.5:.2f}")
        return None
    
    # Check RSI extremes
    rsi_overbought = last['rsi'] > 80  # Changed from 75
    rsi_oversold = last['rsi'] < 20  # Changed from 25
    
    # Relaxed volume threshold
    volume_threshold = asset_config.get('volume_thresholds', {}).get('mean_reversion', 1.5)
    
    # Rest of logic...
```

### 5. Duplicate Detection Refinement

```python
def check_duplicate(self, signal: Signal) -> bool:
    """
    Enhanced duplicate detection with relaxed thresholds
    
    Changes:
    - Increased time window to 10 minutes (from 5)
    - Increased price tolerance to 1.0% (from 0.5%)
    - Allow new signal if RSI changed by >15 points
    - Allow new signal if timeframe differs
    """
    
    time_threshold = timedelta(seconds=self.config.duplicate_window_seconds)  # 600 seconds
    
    for timestamp, prev_signal in self.recent_signals[symbol]:
        # Check same signal type
        if prev_signal.signal_type != signal.signal_type:
            continue
        
        # Allow if different timeframe
        if prev_signal.timeframe != signal.timeframe:
            logger.debug(f"Different timeframe, allowing signal")
            continue
        
        # Check time window
        time_diff = signal.timestamp - timestamp
        if time_diff < time_threshold:
            # Check price proximity
            price_diff_pct = abs(signal.entry_price - prev_signal.entry_price) / prev_signal.entry_price * 100
            
            # Allow if price moved significantly (1.5%)
            if price_diff_pct >= self.config.significant_price_move_pct:  # 1.5%
                logger.debug(f"Significant price move ({price_diff_pct:.2f}%), allowing signal")
                continue
            
            # Allow if RSI changed significantly
            if 'rsi' in signal.indicators and 'rsi' in prev_signal.indicators:
                rsi_diff = abs(signal.indicators['rsi'] - prev_signal.indicators['rsi'])
                if rsi_diff >= 15:
                    logger.debug(f"Significant RSI change ({rsi_diff:.1f}), allowing signal")
                    continue
            
            # Check duplicate tolerance
            if price_diff_pct < self.config.duplicate_price_tolerance_pct:  # 1.0%
                logger.info(f"Duplicate signal: {price_diff_pct:.2f}% price diff within {time_diff.seconds}s")
                return True
    
    return False
```

### 6. Bypass Mode Implementation

```python
class BypassMode:
    """Emergency bypass mode for testing"""
    
    def __init__(self, config: dict, alerter):
        self.enabled = config.get('bypass_mode', {}).get('enabled', False)
        self.auto_disable_hours = config.get('bypass_mode', {}).get('auto_disable_after_hours', 2)
        self.enabled_at = None
        self.alerter = alerter
    
    def enable(self):
        """Enable bypass mode"""
        self.enabled = True
        self.enabled_at = datetime.now()
        
        msg = (
            "⚠️ <b>BYPASS MODE ENABLED</b>\n\n"
            "Quality filters are temporarily disabled.\n"
            f"Will auto-disable in {self.auto_disable_hours} hours.\n\n"
            "All signals will be prefixed with 'BYPASS MODE'"
        )
        self.alerter.send_message(msg)
        logger.warning("BYPASS MODE ENABLED - Quality filters disabled")
    
    def check_auto_disable(self):
        """Check if bypass mode should auto-disable"""
        if self.enabled and self.enabled_at:
            elapsed = (datetime.now() - self.enabled_at).total_seconds() / 3600
            if elapsed >= self.auto_disable_hours:
                self.disable()
    
    def disable(self):
        """Disable bypass mode"""
        self.enabled = False
        self.enabled_at = None
        
        msg = "✅ <b>BYPASS MODE DISABLED</b>\n\nQuality filters re-enabled."
        self.alerter.send_message(msg)
        logger.info("BYPASS MODE DISABLED - Quality filters re-enabled")
    
    def should_bypass_filters(self) -> bool:
        """Check if filters should be bypassed"""
        self.check_auto_disable()
        return self.enabled
```

## Data Models

### DiagnosticReport

```python
@dataclass
class DiagnosticReport:
    """Diagnostic report data model"""
    scanner_name: str
    runtime_hours: float
    last_signal_time: Optional[datetime]
    detection_attempts: Dict[str, int]  # strategy -> count
    successful_detections: Dict[str, int]  # strategy -> count
    filter_rejections: Dict[str, int]  # reason -> count
    data_quality_issues: Dict[str, int]  # issue -> count
    recommendations: List[str]
    
    def to_telegram_message(self) -> str:
        """Format as Telegram message"""
        msg = f"📊 <b>Diagnostic Report: {self.scanner_name}</b>\n\n"
        msg += f"⏱ Runtime: {self.runtime_hours:.1f}h\n"
        msg += f"🎯 Last Signal: {self.last_signal_time.strftime('%H:%M') if self.last_signal_time else 'Never'}\n\n"
        
        # Top 3 strategies by attempts
        top_strategies = sorted(self.detection_attempts.items(), key=lambda x: x[1], reverse=True)[:3]
        msg += "<b>Detection Attempts:</b>\n"
        for strategy, count in top_strategies:
            success = self.successful_detections.get(strategy, 0)
            rate = (success / count * 100) if count > 0 else 0
            msg += f"  • {strategy}: {count} ({rate:.0f}% success)\n"
        
        # Top 3 rejection reasons
        if self.filter_rejections:
            top_rejections = sorted(self.filter_rejections.items(), key=lambda x: x[1], reverse=True)[:3]
            msg += "\n<b>Top Rejection Reasons:</b>\n"
            for reason, count in top_rejections:
                msg += f"  • {reason}: {count}\n"
        
        # Recommendations
        if self.recommendations:
            msg += "\n<b>Recommendations:</b>\n"
            for rec in self.recommendations[:3]:
                msg += f"  {rec}\n"
        
        return msg
```

## Error Handling

### Data Quality Validation

```python
def validate_data_quality(self, data: pd.DataFrame, timeframe: str) -> Tuple[bool, List[str]]:
    """
    Validate data quality before signal detection
    
    Returns:
        (is_valid, issues)
    """
    issues = []
    
    # Check minimum candle count
    if len(data) < 50:
        issues.append(f"Insufficient candles: {len(data)} < 50")
        return False, issues
    
    # Check for NaN in critical indicators
    last = data.iloc[-1]
    critical_indicators = ['close', 'volume', 'ema_9', 'ema_21', 'rsi', 'atr']
    
    for indicator in critical_indicators:
        if indicator in last.index and pd.isna(last[indicator]):
            issues.append(f"NaN value in {indicator}")
    
    # Check timestamp freshness
    expected_interval = self._get_interval_seconds(timeframe)
    age_seconds = (datetime.now() - last['timestamp']).total_seconds()
    
    if age_seconds > expected_interval * 2:
        issues.append(f"Stale data: {age_seconds:.0f}s old (expected < {expected_interval * 2}s)")
    
    # Check volume validity
    if last['volume'] <= 0:
        issues.append("Zero or negative volume")
    
    is_valid = len(issues) == 0
    
    if not is_valid:
        logger.warning(f"Data quality issues for {timeframe}: {', '.join(issues)}")
        if self.diagnostics:
            for issue in issues:
                self.diagnostics.log_data_quality_issue(issue)
    
    return is_valid, issues
```

## Testing Strategy

### Unit Tests

1. **Configuration Validation Tests**
   - Test reasonable bounds checking
   - Test asset-specific override loading
   - Test missing parameter defaults

2. **Threshold Adjustment Tests**
   - Test relaxed volume thresholds
   - Test expanded RSI ranges
   - Test reduced ADX minimums

3. **Duplicate Detection Tests**
   - Test increased time window
   - Test increased price tolerance
   - Test RSI change allowance
   - Test timeframe difference allowance

4. **Diagnostic System Tests**
   - Test detection attempt logging
   - Test filter rejection tracking
   - Test recommendation generation

### Integration Tests

1. **End-to-End Signal Flow**
   - Test signal generation with relaxed thresholds
   - Test quality filter with new configuration
   - Test duplicate detection with new rules

2. **Multi-Scanner Tests**
   - Test asset-specific configuration loading
   - Test per-scanner diagnostic tracking
   - Test daily summary generation

3. **Bypass Mode Tests**
   - Test bypass mode enable/disable
   - Test auto-disable after timeout
   - Test signal prefixing in bypass mode

### Manual Testing Checklist

1. **Configuration Validation**
   - [ ] Start each scanner and verify configuration logging
   - [ ] Check for validation warnings
   - [ ] Verify asset-specific overrides are applied

2. **Signal Generation**
   - [ ] Run scanners for 1 hour and verify signals are generated
   - [ ] Check diagnostic logs for detection attempts
   - [ ] Verify filter rejection reasons are logged

3. **Diagnostic Reports**
   - [ ] Trigger manual diagnostic report
   - [ ] Verify daily summary is sent
   - [ ] Check recommendations are actionable

4. **Bypass Mode**
   - [ ] Enable bypass mode and verify notification
   - [ ] Verify signals are generated without filtering
   - [ ] Verify auto-disable after timeout

## Performance Considerations

### Logging Overhead

- Detection attempt logging adds minimal overhead (~1ms per attempt)
- Use DEBUG level for detailed logs, INFO for summaries
- Rotate diagnostic logs daily to prevent disk space issues

### Memory Usage

- Diagnostic system stores last 1000 detection attempts per scanner
- Recent signals deque limited to 100 entries per symbol
- Daily cleanup of old diagnostic data

### Configuration Reload

- Configuration changes require scanner restart
- Validate configuration on startup to catch issues early
- Log active configuration for troubleshooting

## Deployment Strategy

### Phase 1: Configuration Updates (Low Risk)

1. Update configuration files with relaxed thresholds
2. Add asset-specific overrides
3. Enable diagnostic logging
4. Restart scanners one at a time

### Phase 2: Code Updates (Medium Risk)

1. Deploy diagnostic system
2. Deploy enhanced logging
3. Deploy configuration validation
4. Test on one scanner before rolling out

### Phase 3: Threshold Tuning (Iterative)

1. Monitor diagnostic reports for 24 hours
2. Adjust thresholds based on recommendations
3. Repeat until signal generation is optimal

### Phase 4: Bypass Mode (Emergency Only)

1. Keep bypass mode disabled by default
2. Enable only for troubleshooting
3. Monitor closely when enabled
4. Disable after testing complete

## Monitoring and Alerts

### Real-Time Monitoring

- Log every detection attempt with pass/fail status
- Log every filter rejection with specific reason
- Track detection rate per strategy

### Daily Summary

- Send diagnostic report via Telegram at 18:00 UTC
- Include detection rates, rejection reasons, recommendations
- Highlight scanners with zero signals

### Alert Conditions

- No signals for 4 hours → Send alert
- Detection rate < 5% for any strategy → Send warning
- Data quality issues > 10 per hour → Send alert
- Bypass mode enabled → Send immediate notification

## Security Considerations

- Bypass mode auto-disables after 2 hours for safety
- Configuration validation prevents dangerous threshold values
- Diagnostic logs don't contain sensitive data
- All configuration changes logged for audit trail
