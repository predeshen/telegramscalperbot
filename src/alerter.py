"""Alert delivery via Email and Telegram."""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from src.signal_detector import Signal


logger = logging.getLogger(__name__)


class EmailAlerter:
    """Send trading signal alerts via SMTP email."""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_email: str,
        use_ssl: bool = True
    ):
        """
        Initialize email alerter.
        
        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: From email address
            to_email: Recipient email address
            use_ssl: Use SSL connection
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_email = to_email
        self.use_ssl = use_ssl
        
        self.success_count = 0
        self.failure_count = 0
        
        logger.info(f"Initialized EmailAlerter: {smtp_server}:{smtp_port}")
    
    def send_signal_alert(self, signal: Signal) -> bool:
        """
        Send trading signal alert email.
        
        Args:
            signal: Signal object to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = f"[BTC SCALP] {signal.signal_type} Signal - {signal.timeframe}"
        body = self._format_signal_email(signal)
        
        return self._send_email(subject, body, max_retries=3)
    
    def send_error_alert(self, error: Exception, context: str = "") -> bool:
        """
        Send error alert email.
        
        Args:
            error: Exception that occurred
            context: Additional context about the error
            
        Returns:
            True if sent successfully, False otherwise
        """
        subject = "[BTC SCANNER] Critical Error Alert"
        body = f"""
🚨 Critical Error in BTC Scalping Scanner

Error Type: {type(error).__name__}
Error Message: {str(error)}

Context: {context}

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

Please check the logs for more details.

---
Automated error alert from BTC Scalping Scanner
"""
        
        return self._send_email(subject, body, max_retries=1)
    
    def _format_signal_email(self, signal: Signal) -> str:
        """
        Format signal data into email body.
        
        Args:
            signal: Signal object
            
        Returns:
            Formatted email body string
        """
        # Calculate percentages
        stop_distance = signal.get_stop_distance_percent()
        profit_distance = signal.get_profit_distance_percent()
        volume_ratio = signal.indicators['volume'] / signal.indicators['volume_ma']
        
        # Format signal type with emoji
        signal_emoji = "🟢" if signal.signal_type == "LONG" else "🔴"
        
        body = f"""
{signal_emoji} BTC/USD Scalping Signal Detected

Signal Type: {signal.signal_type}
Timeframe: {signal.timeframe}
Entry Price: ${signal.entry_price:,.2f}
Stop Loss: ${signal.stop_loss:,.2f} (-{stop_distance:.2f}%)
Take Profit: ${signal.take_profit:,.2f} (+{profit_distance:.2f}%)
Risk/Reward: 1:{signal.risk_reward:.2f}

Market Context:
- ATR(14): ${signal.atr:,.2f}
- Market Bias: {signal.market_bias.upper()}
- Confidence: {signal.confidence}/5 factors

Indicators:
- EMA(9): ${signal.indicators['ema_9']:,.2f}
- EMA(21): ${signal.indicators['ema_21']:,.2f}
- EMA(50): ${signal.indicators['ema_50']:,.2f}
- VWAP: ${signal.indicators['vwap']:,.2f}
- RSI(6): {signal.indicators['rsi']:.1f}
- Volume: {signal.indicators['volume']:,.0f} ({volume_ratio:.2f}x avg)

Timestamp: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

---
Automated alert from BTC Scalping Scanner
"""
        return body
    
    def _send_email(self, subject: str, body: str, max_retries: int = 3) -> bool:
        """
        Send email with retry logic.
        
        Args:
            subject: Email subject
            body: Email body
            max_retries: Maximum retry attempts
            
        Returns:
            True if sent successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = self.from_email
                msg['To'] = self.to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                # Connect and send
                if self.use_ssl:
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10)
                else:
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                    server.starttls()
                
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                server.quit()
                
                self.success_count += 1
                logger.info(f"Email sent successfully: {subject}")
                return True
                
            except Exception as e:
                logger.error(f"Email send attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait 5 seconds before retry
                else:
                    self.failure_count += 1
                    return False
        
        return False
    
    def get_success_rate(self) -> float:
        """Calculate email delivery success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total * 100


class TelegramAlerter:
    """Send trading signal alerts via Telegram bot."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram alerter.
        
        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)
        
        if self.enabled:
            try:
                from telegram import Bot
                self.bot = Bot(token=bot_token)
                logger.info("Initialized TelegramAlerter")
            except ImportError:
                logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            logger.info("TelegramAlerter disabled (no credentials provided)")
            self.bot = None
    
    def send_signal_alert(self, signal: Signal) -> bool:
        """
        Send trading signal alert via Telegram.
        
        Args:
            signal: Signal object to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        message = self._format_signal_message(signal)
        return self._send_message(message)
    
    def send_error_alert(self, error: Exception, context: str = "") -> bool:
        """
        Send error alert via Telegram.
        
        Args:
            error: Exception that occurred
            context: Additional context
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        message = f"""
🚨 *Critical Error*

`{type(error).__name__}: {str(error)}`

Context: {context}

Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
"""
        return self._send_message(message)
    
    def _format_signal_message(self, signal: Signal) -> str:
        """
        Format signal data into Telegram message.
        
        Args:
            signal: Signal object
            
        Returns:
            Formatted message string with Markdown
        """
        # Calculate percentages
        stop_distance = signal.get_stop_distance_percent()
        profit_distance = signal.get_profit_distance_percent()
        volume_ratio = signal.indicators['volume'] / signal.indicators['volume_ma']
        breakeven = signal.get_breakeven_price()
        
        # Format signal type with emoji
        signal_emoji = "🟢" if signal.signal_type == "LONG" else "🔴"
        
        message = f"""
{signal_emoji} *BTC/USD {signal.signal_type} SIGNAL*

*📍 ENTRY LEVELS*
Entry: ${signal.entry_price:,.2f}
Stop Loss: ${signal.stop_loss:,.2f} (-{stop_distance:.2f}%)
Take Profit: ${signal.take_profit:,.2f} (+{profit_distance:.2f}%)
Breakeven: ${breakeven:,.2f} (move SL here at 50%)

*📊 TRADE INFO*
R:R: 1:{signal.risk_reward:.2f} | TF: {signal.timeframe}
Market: {signal.market_bias.upper()} | Confidence: {signal.confidence}/5
ATR: ${signal.atr:,.2f}

*🎯 REASONING*
{signal.reasoning}

*📈 TRADE MANAGEMENT*
1️⃣ Enter at ${signal.entry_price:,.2f}
2️⃣ At ${breakeven:,.2f}: Move stop to breakeven
3️⃣ At ${signal.take_profit:,.2f}: Close trade (target hit)
4️⃣ If stopped: Accept loss and wait for next setup

*⏰ {signal.timestamp.strftime('%H:%M:%S UTC')}*
"""
        return message
    
    def send_message(self, message: str, max_retries: int = 3) -> bool:
        """
        Send Telegram message with retry logic (public method).
        
        Args:
            message: Message text (supports Markdown)
            max_retries: Maximum retry attempts
            
        Returns:
            True if sent successfully, False otherwise
        """
        return self._send_message(message, max_retries)
    
    def _send_message(self, message: str, max_retries: int = 3) -> bool:
        """
        Send Telegram message with retry logic.
        
        Args:
            message: Message text (supports Markdown)
            max_retries: Maximum retry attempts
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        for attempt in range(max_retries):
            try:
                import asyncio
                
                # Run async send in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                )
                loop.close()
                
                logger.info("Telegram message sent successfully")
                return True
                
            except Exception as e:
                logger.error(f"Telegram send attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return False
        
        return False


class MultiAlerter:
    """Unified alerter that sends to both Email and Telegram."""
    
    def __init__(self, email_alerter: EmailAlerter, telegram_alerter: Optional[TelegramAlerter] = None):
        """
        Initialize multi-channel alerter.
        
        Args:
            email_alerter: EmailAlerter instance
            telegram_alerter: Optional TelegramAlerter instance
        """
        self.email_alerter = email_alerter
        self.telegram_alerter = telegram_alerter
        
        logger.info("Initialized MultiAlerter")
    
    def send_signal_alert(self, signal: Signal) -> bool:
        """
        Send signal alert to all configured channels.
        
        Args:
            signal: Signal to send
            
        Returns:
            True if at least one channel succeeded
        """
        email_success = self.email_alerter.send_signal_alert(signal)
        
        telegram_success = False
        if self.telegram_alerter and self.telegram_alerter.enabled:
            telegram_success = self.telegram_alerter.send_signal_alert(signal)
        
        return email_success or telegram_success
    
    def send_error_alert(self, error: Exception, context: str = "") -> bool:
        """
        Send error alert to all configured channels.
        
        Args:
            error: Exception that occurred
            context: Additional context
            
        Returns:
            True if at least one channel succeeded
        """
        email_success = self.email_alerter.send_error_alert(error, context)
        
        telegram_success = False
        if self.telegram_alerter and self.telegram_alerter.enabled:
            telegram_success = self.telegram_alerter.send_error_alert(error, context)
        
        return email_success or telegram_success
