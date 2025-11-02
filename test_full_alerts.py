"""Test script to send both Email and Telegram alerts."""
from datetime import datetime
from src.alerter import EmailAlerter, TelegramAlerter, MultiAlerter
from src.signal_detector import Signal

print("=" * 60)
print("BTC Scalping Scanner - Alert System Test")
print("=" * 60)

# Create Email alerter
email = EmailAlerter(
    smtp_server="mail.hashub.co.za",
    smtp_port=465,
    smtp_user="alerts@hashub.co.za",
    smtp_password="Password@2025#!",
    from_email="alerts@hashub.co.za",
    to_email="predeshen@gmail.com",
    use_ssl=True
)

# Create Telegram alerter
telegram = TelegramAlerter(
    bot_token="8276571945:AAFKYdUCEd7Ct405K8BcBWWHyxZe5wGwo7M",
    chat_id="8119046376"
)

# Create Multi alerter
multi_alerter = MultiAlerter(email, telegram)

# Create test signals
long_signal = Signal(
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

short_signal = Signal(
    timestamp=datetime.now(),
    signal_type='SHORT',
    timeframe='1m',
    entry_price=64500.00,
    stop_loss=64750.00,
    take_profit=64250.00,
    atr=250.00,
    risk_reward=1.0,
    market_bias='bearish',
    confidence=4,
    indicators={
        'ema_9': 64450.0,
        'ema_21': 64550.0,
        'ema_50': 64700.0,
        'vwap': 64600.0,
        'rsi': 42.1,
        'volume': 987654.0,
        'volume_ma': 600000.0
    }
)

print("\n1. Testing LONG Signal Alert...")
print("-" * 60)
result = multi_alerter.send_signal_alert(long_signal)
if result:
    print("✅ LONG signal alert sent successfully!")
else:
    print("❌ Failed to send LONG signal alert")

print("\n2. Testing SHORT Signal Alert...")
print("-" * 60)
result = multi_alerter.send_signal_alert(short_signal)
if result:
    print("✅ SHORT signal alert sent successfully!")
else:
    print("❌ Failed to send SHORT signal alert")

print("\n3. Testing Error Alert...")
print("-" * 60)
test_error = Exception("Test error for alert system")
result = multi_alerter.send_error_alert(test_error, "Testing error alert functionality")
if result:
    print("✅ Error alert sent successfully!")
else:
    print("❌ Failed to send error alert")

print("\n" + "=" * 60)
print("Alert System Test Complete!")
print("=" * 60)
print("\nCheck your:")
print("  📧 Email: predeshen@gmail.com")
print("  📱 Telegram: Chat ID 8119046376")
print("\nYou should have received:")
print("  - 1 LONG signal alert")
print("  - 1 SHORT signal alert")
print("  - 1 Error alert")
print("=" * 60)
