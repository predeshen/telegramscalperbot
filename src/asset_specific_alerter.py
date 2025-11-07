"""
Asset-Specific Alert Formatters
Formats alerts with asset-specific context and proper symbol identification
"""
import logging
from typing import Optional
from datetime import datetime

from src.signal_detector import Signal
from src.symbol_context import SymbolContext


logger = logging.getLogger(__name__)


class BTCAlertFormatter:
    """Format BTC-specific alerts"""
    
    def format(self, signal: Signal) -> str:
        """
        Format BTC alert with:
        - ₿ emoji
        - BTC dominance (if available)
        - Entry price (2 decimals)
        - Confidence score
        - Disclaimer about indicative pricing
        
        Args:
            signal: Signal to format
            
        Returns:
            Formatted alert message
        """
        # Get symbol context
        symbol_ctx = signal.symbol_context if hasattr(signal, 'symbol_context') and signal.symbol_context else SymbolContext.from_symbol("BTC")
        
        # Calculate percentages
        stop_distance = signal.get_stop_distance_percent()
        profit_distance = signal.get_profit_distance_percent()
        breakeven = signal.get_breakeven_price()
        
        # Format signal type with emoji
        signal_emoji = "🟢" if signal.signal_type == "LONG" else "🔴"
        
        # Get volume ratio if available
        volume_ratio = ""
        if 'volume' in signal.indicators and 'volume_ma' in signal.indicators:
            vol_ratio = signal.indicators['volume'] / signal.indicators['volume_ma']
            volume_ratio = f" | Vol: {vol_ratio:.2f}x"
        
        message = f"""
{signal_emoji} *{symbol_ctx.emoji} {symbol_ctx.display_name} {signal.signal_type} SIGNAL*

*📍 ENTRY LEVELS*
Entry: ${signal.entry_price:,.2f}
Stop Loss: ${signal.stop_loss:,.2f} (-{stop_distance:.2f}%)
Take Profit: ${signal.take_profit:,.2f} (+{profit_distance:.2f}%)
Breakeven: ${breakeven:,.2f}

*📊 TRADE INFO*
R:R: 1:{signal.risk_reward:.2f} | TF: {signal.timeframe}
Market: {signal.market_bias.upper()} | Confidence: {signal.confidence}/5
ATR: ${signal.atr:,.2f}{volume_ratio}

*🎯 INDICATORS*
EMA(9): ${signal.indicators.get('ema_9', 0):,.2f}
EMA(21): ${signal.indicators.get('ema_21', 0):,.2f}
EMA(50): ${signal.indicators.get('ema_50', 0):,.2f}
RSI: {signal.indicators.get('rsi', 0):.1f}

*⚠️ PRICING DISCLAIMER*
Prices shown are from Yahoo Finance (BTC-USD).
Your broker's execution price may differ slightly.
Always verify price on your trading platform before entering.

*⏰ {signal.timestamp.strftime('%H:%M:%S UTC')}*
"""
        return message


class GoldAlertFormatter:
    """Format Gold-specific alerts"""
    
    def __init__(self, session_manager=None):
        """
        Initialize Gold alert formatter
        
        Args:
            session_manager: Optional SessionManager for session context
        """
        self.session_manager = session_manager
    
    def format(self, signal: Signal) -> str:
        """
        Format Gold alert with:
        - 🥇 emoji
        - Trading session (Asian/London/NY)
        - Spread status
        - Key levels proximity
        - Entry price (2 decimals)
        - Confidence score
        
        Args:
            signal: Signal to format
            
        Returns:
            Formatted alert message
        """
        # Get symbol context
        symbol_ctx = signal.symbol_context if hasattr(signal, 'symbol_context') and signal.symbol_context else SymbolContext.from_symbol("XAUUSD")
        
        # Calculate percentages
        stop_distance = signal.get_stop_distance_percent()
        profit_distance = signal.get_profit_distance_percent()
        breakeven = signal.get_breakeven_price()
        
        # Format signal type with emoji
        signal_emoji = "🟢" if signal.signal_type == "LONG" else "🔴"
        
        # Get session info if available
        session_info = ""
        if self.session_manager:
            session_data = self.session_manager.get_session_info()
            session_info = f"\nSession: {session_data['session']} | {session_data['strategy_focus']}"
        elif hasattr(signal, 'session'):
            session_info = f"\nSession: {signal.session}"
        
        # Get spread info if available
        spread_info = ""
        if hasattr(signal, 'spread_pips') and signal.spread_pips:
            spread_info = f" | Spread: {signal.spread_pips:.1f} pips"
        
        # Get volume ratio if available
        volume_ratio = ""
        if 'volume' in signal.indicators and 'volume_ma' in signal.indicators:
            vol_ratio = signal.indicators['volume'] / signal.indicators['volume_ma']
            volume_ratio = f" | Vol: {vol_ratio:.2f}x"
        
        message = f"""
{signal_emoji} *{symbol_ctx.emoji} {symbol_ctx.display_name} {signal.signal_type} SIGNAL*{session_info}

*📍 ENTRY LEVELS*
Entry: ${signal.entry_price:,.2f}
Stop Loss: ${signal.stop_loss:,.2f} (-{stop_distance:.2f}%)
Take Profit: ${signal.take_profit:,.2f} (+{profit_distance:.2f}%)
Breakeven: ${breakeven:,.2f}

*📊 TRADE INFO*
R:R: 1:{signal.risk_reward:.2f} | TF: {signal.timeframe}
Market: {signal.market_bias.upper()} | Confidence: {signal.confidence}/5
ATR: ${signal.atr:,.2f}{spread_info}{volume_ratio}

*🎯 INDICATORS*
EMA(9): ${signal.indicators.get('ema_9', 0):,.2f}
EMA(21): ${signal.indicators.get('ema_21', 0):,.2f}
EMA(50): ${signal.indicators.get('ema_50', 0):,.2f}
RSI: {signal.indicators.get('rsi', 0):.1f}

*⚠️ PRICING DISCLAIMER*
Prices shown are from Yahoo Finance (GC=F Gold Futures).
Your broker's execution price may differ.
Always verify price on your trading platform before entering.

*⏰ {signal.timestamp.strftime('%H:%M:%S UTC')}*
"""
        return message


class US30AlertFormatter:
    """Format US30-specific alerts"""
    
    def format(self, signal: Signal) -> str:
        """
        Format US30 alert with:
        - 📊 emoji
        - Market hours status
        - Trend strength
        - Entry price (2 decimals)
        - Confidence score
        
        Args:
            signal: Signal to format
            
        Returns:
            Formatted alert message
        """
        # Get symbol context
        symbol_ctx = signal.symbol_context if hasattr(signal, 'symbol_context') and signal.symbol_context else SymbolContext.from_symbol("US30")
        
        # Calculate percentages
        stop_distance = signal.get_stop_distance_percent()
        profit_distance = signal.get_profit_distance_percent()
        breakeven = signal.get_breakeven_price()
        
        # Format signal type with emoji
        signal_emoji = "🟢" if signal.signal_type == "LONG" else "🔴"
        
        # Determine market hours status
        current_hour = datetime.utcnow().hour
        market_status = ""
        if 13 <= current_hour < 20:  # 9:30 AM - 4:00 PM ET
            market_status = "\n🟢 US Market: OPEN"
        else:
            market_status = "\n🔴 US Market: CLOSED (Pre/After hours)"
        
        # Get trend strength from ADX if available
        trend_strength = ""
        if 'adx' in signal.indicators:
            adx = signal.indicators['adx']
            if adx > 25:
                trend_strength = f" | Trend: Strong (ADX {adx:.0f})"
            elif adx > 20:
                trend_strength = f" | Trend: Moderate (ADX {adx:.0f})"
            else:
                trend_strength = f" | Trend: Weak (ADX {adx:.0f})"
        
        # Get volume ratio if available
        volume_ratio = ""
        if 'volume' in signal.indicators and 'volume_ma' in signal.indicators:
            vol_ratio = signal.indicators['volume'] / signal.indicators['volume_ma']
            volume_ratio = f" | Vol: {vol_ratio:.2f}x"
        
        message = f"""
{signal_emoji} *{symbol_ctx.emoji} {symbol_ctx.display_name} {signal.signal_type} SIGNAL*{market_status}

*📍 ENTRY LEVELS*
Entry: ${signal.entry_price:,.2f}
Stop Loss: ${signal.stop_loss:,.2f} (-{stop_distance:.2f}%)
Take Profit: ${signal.take_profit:,.2f} (+{profit_distance:.2f}%)
Breakeven: ${breakeven:,.2f}

*📊 TRADE INFO*
R:R: 1:{signal.risk_reward:.2f} | TF: {signal.timeframe}
Market: {signal.market_bias.upper()} | Confidence: {signal.confidence}/5
ATR: ${signal.atr:,.2f}{trend_strength}{volume_ratio}

*🎯 INDICATORS*
EMA(9): ${signal.indicators.get('ema_9', 0):,.2f}
EMA(21): ${signal.indicators.get('ema_21', 0):,.2f}
EMA(50): ${signal.indicators.get('ema_50', 0):,.2f}
RSI: {signal.indicators.get('rsi', 0):.1f}

*⚠️ PRICING DISCLAIMER*
Prices shown are from Yahoo Finance (^DJI).
Your broker's execution price may differ.
Always verify price on your trading platform before entering.

*⏰ {signal.timestamp.strftime('%H:%M:%S UTC')}*
"""
        return message


class AssetSpecificAlerter:
    """
    Formats and sends alerts with asset-specific context
    """
    
    def __init__(self, telegram_alerter, session_manager=None):
        """
        Initialize asset-specific alerter
        
        Args:
            telegram_alerter: TelegramAlerter instance for sending messages
            session_manager: Optional SessionManager for Gold session context
        """
        self.telegram = telegram_alerter
        self.formatters = {
            "BTC": BTCAlertFormatter(),
            "XAUUSD": GoldAlertFormatter(session_manager),
            "US30": US30AlertFormatter()
        }
        
        logger.info("Initialized AssetSpecificAlerter with formatters for BTC, XAUUSD, US30")
    
    def send_signal_alert(self, signal: Signal) -> bool:
        """
        Send alert with asset-specific formatting
        
        Args:
            signal: Signal to send
            
        Returns:
            True if sent successfully
        """
        # Get symbol from signal
        symbol = "BTC"  # Default
        if hasattr(signal, 'symbol_context') and signal.symbol_context:
            symbol = signal.symbol_context.symbol
        elif hasattr(signal, 'symbol'):
            # Map legacy symbol formats
            symbol_map = {
                "BTC/USD": "BTC",
                "BTC": "BTC",
                "XAU/USD": "XAUUSD",
                "XAUUSD": "XAUUSD",
                "US30": "US30"
            }
            symbol = symbol_map.get(signal.symbol, "BTC")
        
        # Get appropriate formatter
        formatter = self.formatters.get(symbol, self.formatters["BTC"])
        
        # Format alert
        alert_text = formatter.format(signal)
        
        # Send via Telegram
        return self.telegram.send_message(alert_text)
    
    def send_message(self, message: str) -> bool:
        """
        Send a plain text message
        
        Args:
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        return self.telegram.send_message(message)
