"""Configuration loader and validator for BTC Scalping Scanner."""
import json
import os
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class ExchangeConfig:
    """Exchange connection configuration."""
    name: str
    symbol: str
    timeframes: List[str]


@dataclass
class IndicatorConfig:
    """Technical indicator parameters."""
    ema_fast: int
    ema_slow: int
    ema_trend: int
    atr_period: int
    rsi_period: int
    volume_ma_period: int


@dataclass
class SignalRulesConfig:
    """Signal detection rules and thresholds."""
    volume_spike_threshold: float
    rsi_min: int
    rsi_max: int
    stop_loss_atr_multiplier: float
    take_profit_atr_multiplier: float
    duplicate_time_window_minutes: int
    duplicate_price_threshold_percent: float
    adx_min_trend: Optional[float] = None
    enable_extreme_rsi_signals: Optional[bool] = None
    adx_min_momentum_shift: Optional[float] = None
    adx_min_trend_alignment: Optional[float] = None
    rsi_momentum_threshold: Optional[float] = None
    require_price_confirmation: Optional[bool] = None
    volume_reversal_threshold: Optional[float] = None
    mean_reversion_atr_threshold: Optional[float] = None
    max_spread_pips: Optional[float] = None
    acceptable_spread_pips: Optional[float] = None
    key_level_threshold_pips: Optional[float] = None
    stoch_oversold: Optional[int] = None
    stoch_overbought: Optional[int] = None
    stop_loss_points: Optional[float] = None
    take_profit_points_quick: Optional[float] = None
    take_profit_points_extended: Optional[float] = None


@dataclass
class SMTPConfig:
    """SMTP email configuration."""
    server: str
    port: int
    user: str
    password: str
    from_email: str
    to_email: str
    use_ssl: bool


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    enabled: bool
    bot_token: str
    chat_id: str


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    file: str
    rotation: str
    retention_days: int


@dataclass
class H4HVGConfig:
    """H4 HVG strategy configuration."""
    enabled: bool
    min_gap_percent: float
    volume_spike_threshold: float
    atr_multiplier_sl: float
    gap_target_multiplier: float
    min_risk_reward: float
    max_gap_age_candles: int
    rsi_min: int
    rsi_max: int
    require_ema_confluence: bool
    duplicate_time_window_minutes: int
    duplicate_price_threshold_percent: float


@dataclass
class Config:
    """Main application configuration."""
    exchange: ExchangeConfig
    indicators: IndicatorConfig
    signal_rules: SignalRulesConfig
    smtp: SMTPConfig
    telegram: TelegramConfig
    logging: LoggingConfig
    h4_hvg: Optional[H4HVGConfig] = None


class ConfigLoader:
    """Load and validate configuration from JSON file or environment variables."""
    
    @staticmethod
    def load(config_path: str = "config/config.json") -> Config:
        """
        Load configuration from file with environment variable overrides.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            Config object with validated settings
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        # Load from file
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Override with environment variables if present
        config_data = ConfigLoader._apply_env_overrides(config_data)
        
        # Validate and create config objects
        try:
            exchange = ExchangeConfig(**config_data['exchange'])
            indicators = IndicatorConfig(**config_data['indicators'])
            signal_rules = SignalRulesConfig(**config_data['signal_rules'])
            smtp = SMTPConfig(**config_data['smtp'])
            
            # Telegram is optional
            telegram_data = config_data.get('telegram', {
                'enabled': False,
                'bot_token': '',
                'chat_id': ''
            })
            telegram = TelegramConfig(**telegram_data)
            
            logging = LoggingConfig(**config_data['logging'])
            
            # H4 HVG is optional
            h4_hvg = None
            if 'h4_hvg' in config_data:
                h4_hvg = H4HVGConfig(**config_data['h4_hvg'])
            
            config = Config(
                exchange=exchange,
                indicators=indicators,
                signal_rules=signal_rules,
                smtp=smtp,
                telegram=telegram,
                logging=logging,
                h4_hvg=h4_hvg
            )
            
            # Validate configuration
            ConfigLoader._validate(config)
            
            return config
            
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid configuration value: {e}")
    
    @staticmethod
    def _apply_env_overrides(config_data: dict) -> dict:
        """Apply environment variable overrides to config."""
        # SMTP password override
        smtp_password = os.getenv('SMTP_PASSWORD')
        if smtp_password:
            config_data['smtp']['password'] = smtp_password
        
        # Telegram token override
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token:
            if 'telegram' not in config_data:
                config_data['telegram'] = {}
            config_data['telegram']['bot_token'] = telegram_token
        
        # Telegram chat ID override
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if telegram_chat_id:
            if 'telegram' not in config_data:
                config_data['telegram'] = {}
            config_data['telegram']['chat_id'] = telegram_chat_id
        
        return config_data
    
    @staticmethod
    def _validate(config: Config) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If any validation fails
        """
        # Validate exchange
        if config.exchange.name not in ['binance', 'coinbase', 'kraken']:
            raise ValueError(f"Unsupported exchange: {config.exchange.name}")
        
        if not config.exchange.symbol:
            raise ValueError("Exchange symbol cannot be empty")
        
        if not config.exchange.timeframes:
            raise ValueError("At least one timeframe must be specified")
        
        # Validate indicators
        if config.indicators.ema_fast >= config.indicators.ema_slow:
            raise ValueError("Fast EMA period must be less than slow EMA period")
        
        if config.indicators.atr_period < 1:
            raise ValueError("ATR period must be positive")
        
        if config.indicators.rsi_period < 1:
            raise ValueError("RSI period must be positive")
        
        # Validate signal rules
        if config.signal_rules.volume_spike_threshold <= 0:
            raise ValueError("Volume spike threshold must be positive")
        
        if not (0 <= config.signal_rules.rsi_min <= 100):
            raise ValueError("RSI min must be between 0 and 100")
        
        if not (0 <= config.signal_rules.rsi_max <= 100):
            raise ValueError("RSI max must be between 0 and 100")
        
        if config.signal_rules.rsi_min >= config.signal_rules.rsi_max:
            raise ValueError("RSI min must be less than RSI max")
        
        if config.signal_rules.stop_loss_atr_multiplier <= 0:
            raise ValueError("Stop loss ATR multiplier must be positive")
        
        if config.signal_rules.take_profit_atr_multiplier <= 0:
            raise ValueError("Take profit ATR multiplier must be positive")
        
        # Validate SMTP
        if not config.smtp.server:
            raise ValueError("SMTP server cannot be empty")
        
        if not (1 <= config.smtp.port <= 65535):
            raise ValueError("SMTP port must be between 1 and 65535")
        
        if not config.smtp.from_email or '@' not in config.smtp.from_email:
            raise ValueError("Invalid from_email address")
        
        if not config.smtp.to_email or '@' not in config.smtp.to_email:
            raise ValueError("Invalid to_email address")
        
        # Validate Telegram (only if enabled)
        if config.telegram.enabled:
            if not config.telegram.bot_token:
                raise ValueError("Telegram bot_token required when Telegram is enabled")
            if not config.telegram.chat_id:
                raise ValueError("Telegram chat_id required when Telegram is enabled")
        
        # Validate logging
        if config.logging.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid logging level: {config.logging.level}")
        
        if config.logging.retention_days < 1:
            raise ValueError("Log retention days must be positive")
