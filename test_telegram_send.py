"""Test script to send a Telegram message."""
from datetime import datetime
from src.alerter import TelegramAlerter
from src.signal_detector import Signal

# Create Telegram alerter with your credentials
telegram = TelegramAlerter(
    bot_token="8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M",
    chat_id="8119046376"
)

# Create a test signal
test_signal = Signal(
    timestamp=datetime.now(),
    signal_type='LONG',
    timeframe='5m',
    entry_price=65432.50,
    stop_loss=65200.00,
    take_profit=65665.00,
    atr=232.50,
    risk_reward=1.0,
    market_bias='bullish',
    confidence=5,
    indicators={
        'ema_9': 65450.0,
        'ema_21': 65380.0,
        'ema_50': 65100.0,
        'vwap': 65300.0,
        'rsi': 55.3,
        'volume': 1234567.0,
        'volume_ma': 705000.0
    }
)

print("Testing Telegram alert...")
print(f"Bot enabled: {telegram.enabled}")

if telegram.enabled:
    result = telegram.send_signal_alert(test_signal)
    if result:
        print("✅ Telegram message sent successfully!")
    else:
        print("❌ Failed to send Telegram message")
else:
    print("❌ Telegram not enabled (missing credentials)")
