# Design Document

## Overview

The BTC Scalping Scanner is a Python-based real-time signal detection system that continuously monitors BTC/USD market data, applies multi-layered technical analysis with confluence validation, and delivers actionable trade alerts via email. The system is designed for deployment on Linux VMs with minimal dependencies, high reliability, and low latency.

### Key Design Principles

- **Real-time Processing**: Sub-3-second latency from market data to signal generation
- **Confluence-Based Filtering**: Multiple independent signals must align to reduce false positives
- **Fail-Safe Operation**: Automatic reconnection, error recovery, and health monitoring
- **Minimal Dependencies**: Use lightweight libraries to reduce attack surface and deployment complexity
- **Configurable**: All trading parameters and SMTP settings externalized to configuration files

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     BTC Scalping Scanner                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Market     │─────▶│  Indicator   │─────▶│  Signal   │ │
│  │   Data       │      │  Calculator  │      │  Detector │ │
│  │   Client     │      └──────────────┘      └─────┬─────┘ │
│  └──────┬───────┘                                   │       │
│         │                                            │       │
│         │                                            ▼       │
│         │                                    ┌───────────┐  │
│         │                                    │   Email   │  │
│         │                                    │  Alerter  │  │
│         │                                    └───────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │   Logger &   │                                           │
│  │   Health     │                                           │
│  │   Monitor    │                                           │
│  └──────────────┘                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   Exchange API          SMTP Server          Log Files
   (Binance/etc)      (mail.hashub.co.za)   (Rotating)
```

### Technology Stack

- **Language**: Python 3.9+
- **Exchange API**: CCXT library (unified cryptocurrency exchange interface)
- **WebSocket**: websocket-client or exchange-native WebSocket for real-time data
- **Technical Indicators**: pandas-ta or custom implementations
- **Email**: smtplib (Python standard library)
- **Configuration**: JSON/YAML config files
- **Logging**: Python logging module with rotating file handlers
- **Process Management**: systemd service on Linux

## Components and Interfaces

### 1. Market Data Client

**Responsibility**: Connect to exchange, subscribe to BTC/USD streams, maintain candlestick buffers.

**Interface**:
```python
class MarketDataClient:
    def connect() -> bool
    def subscribe_klines(symbol: str, intervals: List[str]) -> None
    def get_latest_candles(interval: str, count: int) -> DataFrame
    def is_connected() -> bool
    def reconnect() -> bool
```

**Implementation Details**:
- Use CCXT library for REST API (historical data initialization)
- Use exchange-native WebSocket for real-time 1m and 5m kline updates
- Maintain in-memory deque buffers (maxlen=200) for each timeframe
- Implement exponential backoff reconnection (1s, 2s, 4s, 8s, 16s max)
- Thread-safe buffer updates using threading.Lock

**Exchange Selection**: Binance (highest BTC/USD liquidity, reliable WebSocket, free tier)

### 2. Indicator Calculator

**Responsibility**: Compute all technical indicators from candlestick data.

**Interface**:
```python
class IndicatorCalculator:
    def calculate_ema(data: DataFrame, period: int) -> Series
    def calculate_vwap(data: DataFrame) -> Series
    def calculate_atr(data: DataFrame, period: int) -> Series
    def calculate_rsi(data: DataFrame, period: int) -> Series
    def calculate_volume_ma(data: DataFrame, period: int) -> Series
    def calculate_all_indicators(data: DataFrame) -> DataFrame
```

**Implementation Details**:
- Use pandas for vectorized calculations (performance)
- EMA: `data['close'].ewm(span=period, adjust=False).mean()`
- VWAP: Reset daily, calculate as `cumsum(price * volume) / cumsum(volume)`
- ATR: Standard true range formula with Wilder smoothing
- RSI: Wilder smoothing on gains/losses
- Cache indicator values, only recalculate on new candle close

### 3. Signal Detector

**Responsibility**: Apply confluence rules, detect long/short setups, generate signals.

**Interface**:
```python
class SignalDetector:
    def detect_signals(candles_1m: DataFrame, candles_5m: DataFrame) -> Optional[Signal]
    def check_bullish_confluence(data: DataFrame) -> bool
    def check_bearish_confluence(data: DataFrame) -> bool
    def is_duplicate_signal(signal: Signal) -> bool
```

**Signal Data Model**:
```python
@dataclass
class Signal:
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str    # "1m" or "5m"
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    risk_reward: float
    market_bias: str  # "bullish", "bearish", "neutral"
    confidence: int   # 3-5 (number of confluence factors)
    indicators: dict  # snapshot of indicator values
```

**Confluence Logic**:

**Bullish (LONG)**:
1. Price > VWAP (session)
2. EMA(9) crosses above EMA(21) in last 2 candles
3. Volume > 1.5 × Volume MA(20)
4. RSI(6) between 30 and 70
5. Price > EMA(50) on higher timeframe (5m if trading 1m, 1h if trading 5m)

**Bearish (SHORT)**: Mirror opposite

**Duplicate Prevention**:
- Store last 50 signals in deque with timestamp
- Block same-type signals within 5 minutes
- Allow if price moved > 0.3% from last signal entry

### 4. Email Alerter

**Responsibility**: Format and send email alerts via SMTP.

**Interface**:
```python
class EmailAlerter:
    def __init__(config: SMTPConfig)
    def send_signal_alert(signal: Signal) -> bool
    def send_error_alert(error: Exception) -> bool
```

**Email Template**:
```
Subject: [BTC SCALP] {LONG/SHORT} Signal - {timeframe}

🚨 BTC/USD Scalping Signal Detected

Signal Type: {LONG/SHORT}
Timeframe: {1m/5m}
Entry Price: ${entry_price}
Stop Loss: ${stop_loss} (-{stop_distance}%)
Take Profit: ${take_profit} (+{profit_distance}%)
Risk/Reward: 1:{risk_reward}

Market Context:
- ATR(14): ${atr}
- Market Bias: {bullish/bearish/neutral}
- Confidence: {3-5}/5 factors

Indicators:
- EMA(9): ${ema9}
- EMA(21): ${ema21}
- VWAP: ${vwap}
- RSI(6): {rsi6}
- Volume: {volume} ({volume_ratio}x avg)

Timestamp: {timestamp} UTC

---
Automated alert from BTC Scalping Scanner
```

**SMTP Configuration** (from user requirements):
- Server: mail.hashub.co.za
- Port: 465 (SSL)
- User: alerts@hashub.co.za
- Password: Password@2025#!
- From: alerts@hashub.co.za
- To: predeshen@gmail.com

**Implementation**:
- Use `smtplib.SMTP_SSL` for secure connection
- Retry logic: 3 attempts with 5-second delays
- Timeout: 10 seconds per attempt
- Log all send attempts and failures

### 5. Logger & Health Monitor

**Responsibility**: Structured logging, health metrics, error tracking.

**Interface**:
```python
class HealthMonitor:
    def record_signal(signal: Signal) -> None
    def record_error(error: Exception) -> None
    def get_health_status() -> HealthStatus
    def get_metrics() -> dict
```

**Logging Strategy**:
- Log Level: INFO for normal operations, ERROR for failures
- Format: `[{timestamp}] [{level}] [{component}] {message}`
- Rotation: Daily rotation, keep 7 days
- Location: `/var/log/btc-scanner/scanner.log`

**Health Metrics**:
- Uptime (seconds since start)
- Total signals generated (long/short counts)
- Last data update timestamp
- Connection status (connected/disconnected)
- Error count (last hour)
- Email success rate

## Data Models

### Configuration Schema

```json
{
  "exchange": {
    "name": "binance",
    "symbol": "BTC/USDT",
    "timeframes": ["1m", "5m"]
  },
  "indicators": {
    "ema_fast": 9,
    "ema_slow": 21,
    "ema_trend": 50,
    "atr_period": 14,
    "rsi_period": 6,
    "volume_ma_period": 20
  },
  "signal_rules": {
    "volume_spike_threshold": 1.5,
    "rsi_min": 30,
    "rsi_max": 70,
    "stop_loss_atr_multiplier": 1.5,
    "take_profit_atr_multiplier": 1.0,
    "duplicate_time_window_minutes": 5,
    "duplicate_price_threshold_percent": 0.3
  },
  "smtp": {
    "server": "mail.hashub.co.za",
    "port": 465,
    "user": "alerts@hashub.co.za",
    "password": "Password@2025#!",
    "from_email": "alerts@hashub.co.za",
    "to_email": "predeshen@gmail.com",
    "use_ssl": true
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/btc-scanner/scanner.log",
    "rotation": "daily",
    "retention_days": 7
  }
}
```

### Candlestick Data Structure

```python
# DataFrame columns for each timeframe buffer
columns = [
    'timestamp',    # Unix timestamp (ms)
    'open',         # Opening price
    'high',         # High price
    'low',          # Low price
    'close',        # Closing price
    'volume',       # Volume in base currency
    'ema_9',        # Calculated indicators...
    'ema_21',
    'ema_50',
    'vwap',
    'atr',
    'rsi',
    'volume_ma'
]
```

## Error Handling

### Error Categories and Responses

1. **Connection Errors** (exchange WebSocket disconnect)
   - Action: Log error, attempt reconnection with exponential backoff
   - Alert: Send email if reconnection fails after 5 attempts
   - Recovery: Continue from last known state, refetch missing candles

2. **Data Errors** (malformed candle data, missing fields)
   - Action: Log warning, skip the malformed candle
   - Alert: Send email if error rate > 10 per hour
   - Recovery: Continue processing next candle

3. **Calculation Errors** (indicator calculation fails, NaN values)
   - Action: Log error with full context (data snapshot)
   - Alert: Send email immediately (critical)
   - Recovery: Skip signal detection for this cycle, continue monitoring

4. **Email Errors** (SMTP connection failure, auth failure)
   - Action: Log error, retry 3 times
   - Alert: Log to file (cannot email about email failure)
   - Recovery: Continue signal detection, queue failed emails for retry

5. **Configuration Errors** (invalid config file, missing parameters)
   - Action: Log error and exit with non-zero code
   - Alert: Print to stderr
   - Recovery: Requires manual intervention, systemd will restart

### Graceful Shutdown

- Catch SIGTERM and SIGINT signals
- Close WebSocket connections cleanly
- Flush log buffers
- Save state (last processed timestamp) to disk
- Exit with code 0

## Testing Strategy

### Unit Tests

**Indicator Calculator Tests**:
- Test EMA calculation against known values (pandas-ta reference)
- Test VWAP calculation with sample data
- Test ATR calculation edge cases (gaps, low volatility)
- Test RSI calculation at boundaries (0, 100)

**Signal Detector Tests**:
- Test bullish confluence with mock data (all conditions met)
- Test bearish confluence with mock data
- Test duplicate detection logic (time window, price threshold)
- Test edge cases (missing indicators, NaN values)

**Email Alerter Tests**:
- Mock SMTP server, verify email content and formatting
- Test retry logic with simulated failures
- Test SSL connection handling

### Integration Tests

**End-to-End Signal Flow**:
- Mock exchange WebSocket with pre-recorded BTC/USD data
- Inject known signal setups (EMA cross + volume spike + VWAP alignment)
- Verify signal detection and email delivery
- Measure latency (data → signal → email)

**Reconnection Tests**:
- Simulate WebSocket disconnect during operation
- Verify automatic reconnection and data continuity
- Verify no duplicate signals during reconnection

### Performance Tests

- **Throughput**: Process 1000 candles/second (well above real-time needs)
- **Latency**: < 2 seconds from candle close to signal generation
- **Memory**: < 200 MB resident memory under normal operation
- **CPU**: < 10% on single core (modern Linux VM)

### Manual Testing Checklist

- [ ] Deploy to Linux VM, verify systemd service starts
- [ ] Monitor logs for 24 hours, check for errors
- [ ] Verify email delivery to predeshen@gmail.com
- [ ] Inject test signal (manual trigger), verify email format
- [ ] Simulate exchange downtime, verify reconnection
- [ ] Check log rotation after 24 hours
- [ ] Verify duplicate signal prevention (trigger same setup twice)

## Deployment

### System Requirements

- Linux VM (Ubuntu 20.04+ or Debian 11+)
- Python 3.9+
- 1 GB RAM minimum
- 10 GB disk space (logs)
- Outbound internet access (exchange API, SMTP)

### Installation Steps

1. Install Python dependencies: `pip install ccxt pandas pandas-ta websocket-client`
2. Create log directory: `sudo mkdir -p /var/log/btc-scanner`
3. Copy config file to `/etc/btc-scanner/config.json`
4. Copy systemd service file to `/etc/systemd/system/btc-scanner.service`
5. Enable service: `sudo systemctl enable btc-scanner`
6. Start service: `sudo systemctl start btc-scanner`

### Systemd Service File

```ini
[Unit]
Description=BTC Scalping Scanner
After=network.target

[Service]
Type=simple
User=btc-scanner
WorkingDirectory=/opt/btc-scanner
ExecStart=/usr/bin/python3 /opt/btc-scanner/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Monitoring

- Check service status: `sudo systemctl status btc-scanner`
- View logs: `sudo journalctl -u btc-scanner -f`
- View application logs: `tail -f /var/log/btc-scanner/scanner.log`
- Health check endpoint: (optional) HTTP server on localhost:8080/health

## Security Considerations

1. **Credential Management**:
   - Store SMTP password in config file with restricted permissions (600)
   - Consider using environment variables or secrets manager for production
   - No exchange API keys needed (read-only public data)

2. **Network Security**:
   - Outbound-only connections (no inbound ports)
   - Use SSL/TLS for SMTP (port 465)
   - Use WSS (WebSocket Secure) for exchange connection

3. **Input Validation**:
   - Validate all exchange data (price > 0, volume >= 0)
   - Sanitize email content (prevent injection)
   - Validate config file schema on startup

4. **Resource Limits**:
   - Limit log file size (rotation)
   - Limit in-memory buffer sizes (deque maxlen)
   - Set timeouts on all network operations

## Future Enhancements

- **Order Flow Integration**: Add order book depth analysis (requires exchange with Level 2 data)
- **Multi-Symbol Support**: Extend to ETH/USD, other pairs
- **Backtesting Module**: Historical signal validation and performance metrics
- **Web Dashboard**: Real-time signal history and performance visualization
- **Telegram Alerts**: Alternative to email for faster notifications
- **Machine Learning**: Train models on historical signals to improve confluence scoring
