"""Signal detection with confluence-based trading logic."""

from dataclasses import dataclass, asdict

from datetime import datetime, timedelta

from collections import deque

from typing import Optional, Dict, List

import pandas as pd

import logging



from src.trend_analyzer import TrendAnalyzer

from src.h4_hvg_detector import GapInfo, H4HVGDetector





logger = logging.getLogger(__name__)





@dataclass
class Signal:
    """Trading signal with entry, stop-loss, and take-profit levels."""
    timestamp: datetime
    signal_type: str  # "LONG" or "SHORT"
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    atr: float
    risk_reward: float
    market_bias: str  # "bullish", "bearish", "neutral"
    confidence: int  # 3-5 (number of confluence factors met)
    indicators: Dict[str, float]  # Snapshot of indicator values
    reasoning: str = ""  # Detailed explanation of why this signal was generated
    symbol: str = "BTC/USD"  # Trading symbol (e.g., "BTC/USD", "XAU/USD", "US30")

    strategy: str = ""  # Strategy name (e.g., "Trend Following", "EMA Crossover")

    trend_direction: Optional[str] = None  # "uptrend" or "downtrend" for trend signals

    swing_points: Optional[int] = None  # Number of swing highs/lows for trend signals

    pullback_depth: Optional[float] = None  # Pullback percentage for trend signals
    
    # H4 HVG specific fields
    gap_info: Optional['GapInfo'] = None  # Gap information for H4 HVG signals
    volume_spike_ratio: Optional[float] = None  # Volume spike ratio for H4 HVG signals
    confluence_factors: Optional[List[str]] = None  # List of confluence factors

    

    def to_dict(self) -> dict:

        """Convert signal to dictionary."""

        return asdict(self)

    

    def get_stop_distance_percent(self) -> float:

        """Calculate stop-loss distance as percentage of entry."""

        return abs(self.entry_price - self.stop_loss) / self.entry_price * 100

    

    def get_profit_distance_percent(self) -> float:

        """Calculate take-profit distance as percentage of entry."""

        return abs(self.take_profit - self.entry_price) / self.entry_price * 100

    

    def get_breakeven_price(self) -> float:

        """Calculate breakeven price (50% to target)."""

        if self.signal_type == "LONG":

            return self.entry_price + (self.take_profit - self.entry_price) * 0.5

        else:

            return self.entry_price - (self.entry_price - self.take_profit) * 0.5





class SignalDetector:

    """

    Detect trading signals using confluence of multiple technical indicators.

    

    Implements bullish/bearish signal detection with duplicate prevention.

    """

    

    def __init__(

        self,

        volume_spike_threshold: float = 1.5,

        rsi_min: int = 30,

        rsi_max: int = 70,

        stop_loss_atr_multiplier: float = 1.5,

        take_profit_atr_multiplier: float = 1.0,

        duplicate_time_window_minutes: int = 5,

        duplicate_price_threshold_percent: float = 0.3

    ):

        """

        Initialize signal detector.

        

        Args:

            volume_spike_threshold: Minimum volume ratio vs MA to confirm signal

            rsi_min: Minimum RSI value (avoid oversold)

            rsi_max: Maximum RSI value (avoid overbought)

            stop_loss_atr_multiplier: ATR multiplier for stop-loss distance

            take_profit_atr_multiplier: ATR multiplier for take-profit distance

            duplicate_time_window_minutes: Time window to block duplicate signals

            duplicate_price_threshold_percent: Price move % to allow new signal

        """

        self.volume_spike_threshold = volume_spike_threshold

        self.rsi_min = rsi_min

        self.rsi_max = rsi_max

        self.stop_loss_atr_multiplier = stop_loss_atr_multiplier

        self.take_profit_atr_multiplier = take_profit_atr_multiplier

        self.duplicate_time_window_minutes = duplicate_time_window_minutes

        self.duplicate_price_threshold_percent = duplicate_price_threshold_percent

        

        # Signal history for duplicate detection

        self.signal_history: deque = deque(maxlen=50)
        
        # H4 HVG detector (will be initialized when needed)
        self.h4_hvg_detector = None

        

        logger.info("Initialized SignalDetector with confluence rules")
    
    def configure_h4_hvg(self, h4_hvg_config: dict, symbol: str) -> None:
        """
        Configure H4 HVG detector with specific settings.
        
        Args:
            h4_hvg_config: H4 HVG configuration dictionary
            symbol: Trading symbol
        """
        try:
            self.h4_hvg_detector = H4HVGDetector(config=h4_hvg_config, symbol=symbol)
            logger.info(f"H4HVGDetector configured for {symbol}")
        except Exception as e:
            logger.error(f"Error configuring H4HVGDetector: {e}")

    

    def detect_signals(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Detect trading signals from candlestick data with indicators.

        

        Args:

            data: DataFrame with OHLCV and calculated indicators

            timeframe: Timeframe string (e.g., '1m', '5m')

            symbol: Trading symbol (e.g., 'BTC/USD', 'XAU/USD', 'US30')

            

        Returns:

            Signal object if detected, None otherwise

        """

        if data.empty or len(data) < 3:

            return None

        

        # Clean expired signals from history

        self._clean_expired_signals()

        

        # Check for bullish signal

        bullish_signal = self._check_bullish_confluence(data, timeframe, symbol)

        if bullish_signal and not self._is_duplicate_signal(bullish_signal):

            self.signal_history.append(bullish_signal)

            logger.info(f"LONG signal detected on {timeframe}: {bullish_signal.entry_price}")

            return bullish_signal

        

        # Check for bearish signal

        bearish_signal = self._check_bearish_confluence(data, timeframe, symbol)

        if bearish_signal and not self._is_duplicate_signal(bearish_signal):

            self.signal_history.append(bearish_signal)

            logger.info(f"SHORT signal detected on {timeframe}: {bearish_signal.entry_price}")

            return bearish_signal

        

        # Check for trend-following signal if no crossover signal found

        trend_signal = self._detect_trend_following(data, timeframe, symbol)

        if trend_signal and not self._is_duplicate_signal(trend_signal):

            self.signal_history.append(trend_signal)

            logger.info(f"{trend_signal.signal_type} trend-following signal detected on {timeframe}: {trend_signal.entry_price}")

            return trend_signal

        

        # Check for extreme RSI reversal signals (like the BTC drop)
        if self.config.get('signal_rules', {}).get('enable_extreme_rsi_signals', False):
            extreme_rsi_signal = self._detect_extreme_rsi_reversal(data, timeframe, symbol)
            if extreme_rsi_signal and not self._is_duplicate_signal(extreme_rsi_signal):
                self.signal_history.append(extreme_rsi_signal)
                logger.info(f"{extreme_rsi_signal.signal_type} extreme RSI signal detected on {timeframe}: {extreme_rsi_signal.entry_price}")
                return extreme_rsi_signal

        # Check for H4 HVG signal on 4-hour timeframe
        if timeframe == '4h':
            hvg_signal = self._detect_h4_hvg(data, timeframe, symbol)
            if hvg_signal and not self._is_duplicate_signal(hvg_signal):
                self.signal_history.append(hvg_signal)
                logger.info(f"H4 HVG {hvg_signal.signal_type} signal detected on {timeframe}: {hvg_signal.entry_price}")
                return hvg_signal

        return None
    
    def _detect_h4_hvg(self, data: pd.DataFrame, timeframe: str, symbol: str) -> Optional[Signal]:
        """
        Detect H4 HVG signals using the H4HVGDetector.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal object if H4 HVG detected, None otherwise
        """
        try:
            # Initialize H4 HVG detector if not already done
            if self.h4_hvg_detector is None:
                # Use default configuration for now
                # In production, this should come from the main configuration
                self.h4_hvg_detector = H4HVGDetector(symbol=symbol)
                logger.info(f"Initialized H4HVGDetector for {symbol}")
            
            # Generate H4 HVG signal
            signal = self.h4_hvg_detector.generate_h4_hvg_signal(data, timeframe, symbol)
            
            if signal:
                # Check for duplicates using H4 HVG detector's own duplicate detection
                if not self.h4_hvg_detector.is_duplicate_signal(signal):
                    # Add to H4 HVG detector's history
                    self.h4_hvg_detector.add_signal_to_history(signal)
                    return signal
                else:
                    logger.debug("H4 HVG signal rejected as duplicate")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting H4 HVG signal: {e}")
            return None

    

    def _check_bullish_confluence(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Check for bullish (LONG) signal with confluence validation.

        

        Confluence factors:

        1. Price > VWAP

        2. EMA(9) crosses above EMA(21) in last 2 candles

        3. Volume > 1.5x volume MA

        4. RSI between 30 and 70

        5. Price > EMA(50) for bullish bias

        

        Args:

            data: DataFrame with indicators

            timeframe: Timeframe string

            

        Returns:

            Signal object if all confluence met, None otherwise

        """

        try:

            # Get last few rows

            last = data.iloc[-1]

            prev = data.iloc[-2] if len(data) >= 2 else None

            

            if prev is None:

                return None

            

            confluence_count = 0

            

            # Factor 1: Price > VWAP

            if last['close'] > last['vwap']:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 2: EMA(9) crosses above EMA(21)

            ema_cross = (

                last['ema_9'] > last['ema_21'] and

                prev['ema_9'] <= prev['ema_21']

            )

            if ema_cross:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 3: Volume spike

            if last['volume'] > (last['volume_ma'] * self.volume_spike_threshold):

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 4: RSI in valid range

            if self.rsi_min <= last['rsi'] <= self.rsi_max:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 5: Bullish bias (price > EMA50)

            market_bias = "neutral"

            if last['close'] > last['ema_50']:

                confluence_count += 1

                market_bias = "bullish"

            

            # All critical factors met, create signal

            entry_price = last['close']

            atr = last['atr']

            stop_loss = entry_price - (atr * self.stop_loss_atr_multiplier)

            take_profit = entry_price + (atr * self.take_profit_atr_multiplier)

            risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)

            

            # Generate reasoning

            reasoning = self._generate_reasoning("LONG", last, prev, confluence_count, market_bias)

            

            signal = Signal(

                timestamp=last['timestamp'],

                signal_type="LONG",

                timeframe=timeframe,

                symbol=symbol,

                entry_price=entry_price,

                stop_loss=stop_loss,

                take_profit=take_profit,

                atr=atr,

                risk_reward=risk_reward,

                market_bias=market_bias,

                confidence=confluence_count,

                indicators={

                    'ema_9': last['ema_9'],

                    'ema_21': last['ema_21'],

                    'ema_50': last['ema_50'],

                    'vwap': last['vwap'],

                    'rsi': last['rsi'],

                    'volume': last['volume'],

                    'volume_ma': last['volume_ma']

                },

                reasoning=reasoning

            )

            

            return signal

            

        except Exception as e:

            logger.error(f"Error checking bullish confluence: {e}")

            return None

    

    def _check_bearish_confluence(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Check for bearish (SHORT) signal with confluence validation.

        

        Confluence factors:

        1. Price < VWAP

        2. EMA(9) crosses below EMA(21) in last 2 candles

        3. Volume > 1.5x volume MA

        4. RSI between 30 and 70

        5. Price < EMA(50) for bearish bias

        

        Args:

            data: DataFrame with indicators

            timeframe: Timeframe string

            

        Returns:

            Signal object if all confluence met, None otherwise

        """

        try:

            # Get last few rows

            last = data.iloc[-1]

            prev = data.iloc[-2] if len(data) >= 2 else None

            

            if prev is None:

                return None

            

            confluence_count = 0

            

            # Factor 1: Price < VWAP

            if last['close'] < last['vwap']:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 2: EMA(9) crosses below EMA(21)

            ema_cross = (

                last['ema_9'] < last['ema_21'] and

                prev['ema_9'] >= prev['ema_21']

            )

            if ema_cross:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 3: Volume spike

            if last['volume'] > (last['volume_ma'] * self.volume_spike_threshold):

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 4: RSI in valid range

            if self.rsi_min <= last['rsi'] <= self.rsi_max:

                confluence_count += 1

            else:

                return None  # Critical factor

            

            # Factor 5: Bearish bias (price < EMA50)

            market_bias = "neutral"

            if last['close'] < last['ema_50']:

                confluence_count += 1

                market_bias = "bearish"

            

            # All critical factors met, create signal

            entry_price = last['close']

            atr = last['atr']

            stop_loss = entry_price + (atr * self.stop_loss_atr_multiplier)

            take_profit = entry_price - (atr * self.take_profit_atr_multiplier)

            risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)

            

            # Generate reasoning

            reasoning = self._generate_reasoning("SHORT", last, prev, confluence_count, market_bias)

            

            signal = Signal(

                timestamp=last['timestamp'],

                signal_type="SHORT",

                timeframe=timeframe,

                symbol=symbol,

                entry_price=entry_price,

                stop_loss=stop_loss,

                take_profit=take_profit,

                atr=atr,

                risk_reward=risk_reward,

                market_bias=market_bias,

                confidence=confluence_count,

                indicators={

                    'ema_9': last['ema_9'],

                    'ema_21': last['ema_21'],

                    'ema_50': last['ema_50'],

                    'vwap': last['vwap'],

                    'rsi': last['rsi'],

                    'volume': last['volume'],

                    'volume_ma': last['volume_ma']

                },

                reasoning=reasoning

            )

            

            return signal

            

        except Exception as e:

            logger.error(f"Error checking bearish confluence: {e}")

            return None

    

    def _is_duplicate_signal(self, signal: Signal) -> bool:

        """

        Check if signal is a duplicate of recent signal.

        

        Args:

            signal: Signal to check

            

        Returns:

            True if duplicate, False otherwise

        """

        time_threshold = timedelta(minutes=self.duplicate_time_window_minutes)

        

        for prev_signal in self.signal_history:

            # Check same signal type

            if prev_signal.signal_type != signal.signal_type:

                continue

            

            # Check time window

            time_diff = signal.timestamp - prev_signal.timestamp

            if time_diff < time_threshold:

                # Check price movement

                price_change_percent = abs(

                    signal.entry_price - prev_signal.entry_price

                ) / prev_signal.entry_price * 100

                

                if price_change_percent < self.duplicate_price_threshold_percent:

                    logger.debug(f"Duplicate signal blocked: {signal.signal_type} within {time_diff.seconds}s")

                    return True

        

        return False

    

    def _clean_expired_signals(self) -> None:

        """Remove signals older than 30 minutes from history."""

        cutoff_time = datetime.now() - timedelta(minutes=30)

        

        # Filter out expired signals

        self.signal_history = deque(

            [s for s in self.signal_history if s.timestamp > cutoff_time],

            maxlen=50

        )

    

    def _detect_trend_following(self, data: pd.DataFrame, timeframe: str, symbol: str = "BTC/USD") -> Optional[Signal]:

        """

        Detect trend-following signals based on swing points and pullbacks.

        

        Strategy:

        1. Detect swing points to identify trend

        2. Verify EMA alignment with trend

        3. Wait for pullback to EMA(21)

        4. Confirm bounce with volume

        5. Validate RSI range

        

        Args:

            data: DataFrame with OHLCV and indicators

            timeframe: Timeframe string

            

        Returns:

            Signal with strategy="Trend Following" if detected, None otherwise

        """

        try:

            if len(data) < 50:

                return None

            

            # Detect swing points

            swing_data = TrendAnalyzer.detect_swing_points(data, lookback=5)

            

            # Check for uptrend

            is_uptrend = TrendAnalyzer.is_uptrend(swing_data, min_swings=3)

            is_downtrend = TrendAnalyzer.is_downtrend(swing_data, min_swings=3)

            

            if not (is_uptrend or is_downtrend):

                return None

            

            trend_direction = "uptrend" if is_uptrend else "downtrend"

            

            # Check if market is consolidating (skip if ATR declining)

            if TrendAnalyzer.is_consolidating(data, periods=3):

                logger.debug(f"Skipping trend signal: market consolidating on {timeframe}")

                return None

            

            # Verify EMA alignment

            if not TrendAnalyzer.is_ema_aligned(data, trend_direction):

                return None

            

            # Get last candles

            last = data.iloc[-1]

            prev = data.iloc[-2]

            

            # Calculate pullback depth

            pullback_depth = TrendAnalyzer.calculate_pullback_depth(data, trend_direction)

            

            # Reject if pullback too deep (> 61.8%)

            if pullback_depth > 61.8:

                logger.debug(f"Skipping trend signal: pullback too deep ({pullback_depth:.1f}%) on {timeframe}")

                return None

            

            # Check volume confirmation (at least 1.2x average)

            if last['volume'] < (last['volume_ma'] * 1.2):

                return None

            

            # Check if volume is declining (reduce confidence)

            volume_declining = (

                last['volume'] < prev['volume'] and

                prev['volume'] < data.iloc[-3]['volume']

            )

            

            if volume_declining:

                logger.debug(f"Skipping trend signal: volume declining on {timeframe}")

                return None

            

            # Detect pullback entry for uptrend

            if is_uptrend:

                # Check RSI range (40-80 for uptrends)

                if not (40 <= last['rsi'] <= 80):

                    return None

                

                # Check if price pulled back to EMA(21) and bounced

                ema_21 = last.get('ema_21', last.get('ema_20'))

                if pd.isna(ema_21):

                    return None

                

                # Price should be near EMA(21) (within 1 ATR)

                distance_from_ema = abs(last['close'] - ema_21)

                if distance_from_ema > last['atr']:

                    return None

                

                # Price should be bouncing up (close > open)

                if last['close'] <= last['open']:

                    return None

                

                # Generate LONG signal

                entry_price = last['close']

                atr = last['atr']

                stop_loss = entry_price - (atr * 1.5)

                

                # Stronger trend gets larger target

                if last['rsi'] > 60:

                    take_profit = entry_price + (atr * 3.0)

                else:

                    take_profit = entry_price + (atr * 2.5)

                

                risk_reward = (take_profit - entry_price) / (entry_price - stop_loss)

                

                # Count swing points for confidence

                total_swings = swing_data['higher_highs'] + swing_data['higher_lows']

                

                # Generate reasoning

                reasoning = self._generate_trend_reasoning(

                    "LONG", last, swing_data, pullback_depth, total_swings

                )

                

                signal = Signal(

                    timestamp=last['timestamp'],

                    signal_type="LONG",

                    timeframe=timeframe,

                    symbol=symbol,

                    entry_price=entry_price,

                    stop_loss=stop_loss,

                    take_profit=take_profit,

                    atr=atr,

                    risk_reward=risk_reward,

                    market_bias="bullish",

                    confidence=4,  # Trend signals are high confidence

                    indicators={

                        'ema_9': last.get('ema_9'),

                        'ema_21': ema_21,

                        'ema_50': last['ema_50'],

                        'vwap': last.get('vwap'),

                        'rsi': last['rsi'],

                        'volume': last['volume'],

                        'volume_ma': last['volume_ma']

                    },

                    reasoning=reasoning,

                    strategy="Trend Following",

                    trend_direction=trend_direction,

                    swing_points=total_swings,

                    pullback_depth=pullback_depth

                )

                

                return signal

            

            # Detect pullback entry for downtrend

            elif is_downtrend:

                # Check RSI range (20-60 for downtrends)

                if not (20 <= last['rsi'] <= 60):

                    return None

                

                # Check if price rallied to EMA(21) and rejected

                ema_21 = last.get('ema_21', last.get('ema_20'))

                if pd.isna(ema_21):

                    return None

                

                # Price should be near EMA(21) (within 1 ATR)

                distance_from_ema = abs(last['close'] - ema_21)

                if distance_from_ema > last['atr']:

                    return None

                

                # Price should be rejecting down (close < open)

                if last['close'] >= last['open']:

                    return None

                

                # Generate SHORT signal

                entry_price = last['close']

                atr = last['atr']

                stop_loss = entry_price + (atr * 1.5)

                

                # Stronger trend gets larger target

                if last['rsi'] < 40:

                    take_profit = entry_price - (atr * 3.0)

                else:

                    take_profit = entry_price - (atr * 2.5)

                

                risk_reward = (entry_price - take_profit) / (stop_loss - entry_price)

                

                # Count swing points for confidence

                total_swings = swing_data['lower_highs'] + swing_data['lower_lows']

                

                # Generate reasoning

                reasoning = self._generate_trend_reasoning(

                    "SHORT", last, swing_data, pullback_depth, total_swings

                )

                

                signal = Signal(

                    timestamp=last['timestamp'],

                    signal_type="SHORT",

                    timeframe=timeframe,

                    symbol=symbol,

                    entry_price=entry_price,

                    stop_loss=stop_loss,

                    take_profit=take_profit,

                    atr=atr,

                    risk_reward=risk_reward,

                    market_bias="bearish",

                    confidence=4,  # Trend signals are high confidence

                    indicators={

                        'ema_9': last.get('ema_9'),

                        'ema_21': ema_21,

                        'ema_50': last['ema_50'],

                        'vwap': last.get('vwap'),

                        'rsi': last['rsi'],

                        'volume': last['volume'],

                        'volume_ma': last['volume_ma']

                    },

                    reasoning=reasoning,

                    strategy="Trend Following",

                    trend_direction=trend_direction,

                    swing_points=total_swings,

                    pullback_depth=pullback_depth

                )

                

                return signal

            

            return None

            

        except Exception as e:

            logger.error(f"Error in trend-following detection: {e}")

            return None

    

    def _generate_trend_reasoning(self, signal_type: str, last: pd.Series,

                                  swing_data: Dict, pullback_depth: float,

                                  swing_points: int) -> str:

        """

        Generate reasoning for trend-following signals.

        

        Args:

            signal_type: "LONG" or "SHORT"

            last: Last candle data

            swing_data: Swing point data from TrendAnalyzer

            pullback_depth: Pullback percentage

            swing_points: Total number of swing points

            

        Returns:

            Formatted reasoning string

        """

        reasons = []

        

        # Strategy intro

        reasons.append("STRATEGY: Trend Following")

        

        # Trend identification

        if signal_type == "LONG":

            reasons.append(f"UPTREND IDENTIFIED: {swing_points} swing points detected")

            reasons.append(f"    Higher Highs: {swing_data['higher_highs']}")

            reasons.append(f"    Higher Lows: {swing_data['higher_lows']}")

            reasons.append(f"    Trend strength: Strong and established")

        else:

            reasons.append(f"DOWNTREND IDENTIFIED: {swing_points} swing points detected")

            reasons.append(f"    Lower Highs: {swing_data['lower_highs']}")

            reasons.append(f"    Lower Lows: {swing_data['lower_lows']}")

            reasons.append(f"    Trend strength: Strong and established")

        

        # Pullback entry

        ema_21 = last.get('ema_21', last.get('ema_20'))

        if signal_type == "LONG":

            reasons.append(f"\nPULLBACK ENTRY: Price pulled back {pullback_depth:.1f}% and bounced at EMA(21)")

            reasons.append(f"    EMA(21): ${ema_21:.2f} acting as dynamic support")

            reasons.append(f"    Pullback healthy (< 61.8%), trend intact")

        else:

            reasons.append(f"\nRALLY REJECTION: Price rallied {pullback_depth:.1f}% and rejected at EMA(21)")

            reasons.append(f"    EMA(21): ${ema_21:.2f} acting as dynamic resistance")

            reasons.append(f"    Rally contained (< 61.8%), trend intact")

        

        # Volume confirmation

        volume_ratio = last['volume'] / last['volume_ma']

        reasons.append(f"\nVOLUME CONFIRMATION: {volume_ratio:.2f}x average volume")

        reasons.append(f"    Confirms genuine interest at this level")

        

        # RSI momentum

        reasons.append(f"\n MOMENTUM: RSI at {last['rsi']:.1f}")

        if signal_type == "LONG":

            if last['rsi'] > 60:

                reasons.append(f"    Strong bullish momentum, extended target justified")

            else:

                reasons.append(f"    Healthy momentum, room to run higher")

        else:

            if last['rsi'] < 40:

                reasons.append(f"    Strong bearish momentum, extended target justified")

            else:

                reasons.append(f"    Healthy momentum, room to fall further")

        

        # Why enter NOW

        reasons.append(f"\nWHY ENTER NOW:")

        reasons.append(f"    Established trend with {swing_points} confirmed swing points")

        reasons.append(f"    Optimal pullback entry at key moving average")

        reasons.append(f"    Volume confirms buyers/sellers stepping in")

        reasons.append(f"    Risk-reward favorable with trend on our side")

        

        return "\n".join(reasons)

    

    def _generate_reasoning(self, signal_type: str, last: pd.Series, prev: pd.Series, 

                           confluence_count: int, market_bias: str) -> str:

        """

        Generate detailed reasoning for why this signal was generated.

        

        Args:

            signal_type: "LONG" or "SHORT"

            last: Last candle data

            prev: Previous candle data

            confluence_count: Number of confluence factors met

            market_bias: Market bias string

            

        Returns:

            Formatted reasoning string

        """

        reasons = []

        

        # 1. Market Bias

        if signal_type == "LONG":

            reasons.append(f"BULLISH BIAS: Price trading above VWAP (${last['vwap']:.2f}), indicating institutional buying pressure")

            if market_bias == "bullish":

                reasons.append(f" Trend Confirmation: Price above EMA(50) at ${last['ema_50']:.2f}, confirming uptrend")

        else:

            reasons.append(f"BEARISH BIAS: Price trading below VWAP (${last['vwap']:.2f}), indicating institutional selling pressure")

            if market_bias == "bearish":

                reasons.append(f" Trend Confirmation: Price below EMA(50) at ${last['ema_50']:.2f}, confirming downtrend")

        

        # 2. EMA Crossover

        if signal_type == "LONG":

            reasons.append(f"MOMENTUM SHIFT: EMA(9) crossed above EMA(21), signaling short-term bullish momentum")

            reasons.append(f"    EMA(9): ${last['ema_9']:.2f} > EMA(21): ${last['ema_21']:.2f}")

        else:

            reasons.append(f"MOMENTUM SHIFT: EMA(9) crossed below EMA(21), signaling short-term bearish momentum")

            reasons.append(f"    EMA(9): ${last['ema_9']:.2f} < EMA(21): ${last['ema_21']:.2f}")

        

        # 3. Volume Confirmation

        volume_ratio = last['volume'] / last['volume_ma']

        reasons.append(f"VOLUME SPIKE: {volume_ratio:.2f}x average volume confirms genuine breakout")

        reasons.append(f"    Current: {last['volume']:,.0f} vs Avg: {last['volume_ma']:,.0f}")

        

        # 4. RSI Validation

        reasons.append(f" MOMENTUM HEALTHY: RSI at {last['rsi']:.1f} - not overextended, room to run")

        if 40 <= last['rsi'] <= 60:

            reasons.append(f"    RSI in neutral zone, ideal for new trend development")

        

        # 5. Why to Enter NOW

        if signal_type == "LONG":

            reasons.append(f"\nWHY BUY NOW:")

            reasons.append(f"    All {confluence_count} confluence factors aligned simultaneously")

            reasons.append(f"    Momentum turning bullish after pullback")

            reasons.append(f"    Institutional buyers (VWAP) supporting price")

            reasons.append(f"    Volume confirms real buying interest, not a fake move")

        else:

            reasons.append(f"\nWHY SELL NOW:")

            reasons.append(f"    All {confluence_count} confluence factors aligned simultaneously")

            reasons.append(f"    Momentum turning bearish after rally")

            reasons.append(f"    Institutional sellers (VWAP) pressuring price")

            reasons.append(f"    Volume confirms real selling interest, not a fake move")

        

        return "\n".join(reasons)

    def _detect_extreme_rsi_reversal(self, data: pd.DataFrame, timeframe: str, symbol: str) -> Optional[Signal]:
        """
        Detect extreme RSI reversal signals for strong momentum moves.
        
        This catches signals like the BTC drop where RSI goes to extreme levels
        with strong ADX indicating a powerful trend that may continue.
        
        Args:
            data: DataFrame with OHLCV and indicators
            timeframe: Timeframe string
            symbol: Trading symbol
            
        Returns:
            Signal object if detected, None otherwise
        """
        try:
            if len(data) < 3:
                return None
            
            last = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Check for required indicators
            required_indicators = ['rsi', 'adx', 'atr', 'volume', 'volume_ma']
            if not all(ind in last.index for ind in required_indicators):
                return None
            
            # Get configuration
            adx_min = self.config.get('signal_rules', {}).get('adx_min_trend', 20)
            volume_threshold = self.config.get('signal_rules', {}).get('volume_spike_threshold', 0.8)
            
            # Check for strong trend (high ADX)
            if last['adx'] < adx_min:
                return None
            
            # Check volume
            volume_ratio = last['volume'] / last['volume_ma']
            if volume_ratio < volume_threshold:
                return None
            
            # Extreme oversold with strong bearish momentum (like BTC drop)
            if (last['rsi'] <= 15 and  # Extremely oversold
                last['rsi'] < prev['rsi'] and  # Still declining
                last['adx'] > 30):  # Strong trend
                
                logger.info(f"[{timeframe}] Extreme RSI bearish continuation detected - RSI: {last['rsi']:.1f}, ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry + (last['atr'] * self.config['signal_rules']['stop_loss_atr_multiplier'])
                take_profit = entry - (last['atr'] * self.config['signal_rules']['take_profit_atr_multiplier'])
                
                # Calculate risk/reward
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)
                risk_reward = reward / risk if risk > 0 else 0
                
                # Generate reasoning
                reasoning = f"""🔥 EXTREME RSI BEARISH MOMENTUM 🔥
                
📉 OVERSOLD CONTINUATION SIGNAL:
• RSI at extreme level: {last['rsi']:.1f} (< 15)
• Strong bearish trend: ADX {last['adx']:.1f} (> 30)
• Volume confirmation: {volume_ratio:.2f}x average
• Price momentum: Still declining

⚡ MOMENTUM ANALYSIS:
• This is NOT a reversal signal - it's a continuation
• Extreme RSI with high ADX = powerful trend in motion
• Volume confirms institutional participation
• Similar to major market crashes/breakdowns

🎯 TRADE RATIONALE:
• Ride the momentum while it's strong
• Exit when RSI starts to recover or ADX weakens
• High probability continuation pattern
• Risk/Reward: {risk_reward:.2f}:1"""

                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="SHORT",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bearish",
                    confidence=4,  # High confidence for extreme moves
                    indicators=last.to_dict(),
                    reasoning=reasoning,
                    symbol=symbol,
                    strategy="Extreme RSI Continuation"
                )
                
                return signal
            
            # Extreme overbought with strong bullish momentum
            elif (last['rsi'] >= 85 and  # Extremely overbought
                  last['rsi'] > prev['rsi'] and  # Still rising
                  last['adx'] > 30):  # Strong trend
                
                logger.info(f"[{timeframe}] Extreme RSI bullish continuation detected - RSI: {last['rsi']:.1f}, ADX: {last['adx']:.1f}, Volume: {volume_ratio:.2f}x")
                
                entry = last['close']
                stop_loss = entry - (last['atr'] * self.config['signal_rules']['stop_loss_atr_multiplier'])
                take_profit = entry + (last['atr'] * self.config['signal_rules']['take_profit_atr_multiplier'])
                
                # Calculate risk/reward
                risk = abs(stop_loss - entry)
                reward = abs(take_profit - entry)
                risk_reward = reward / risk if risk > 0 else 0
                
                # Generate reasoning
                reasoning = f"""🚀 EXTREME RSI BULLISH MOMENTUM 🚀
                
📈 OVERBOUGHT CONTINUATION SIGNAL:
• RSI at extreme level: {last['rsi']:.1f} (> 85)
• Strong bullish trend: ADX {last['adx']:.1f} (> 30)
• Volume confirmation: {volume_ratio:.2f}x average
• Price momentum: Still rising

⚡ MOMENTUM ANALYSIS:
• This is NOT a reversal signal - it's a continuation
• Extreme RSI with high ADX = powerful trend in motion
• Volume confirms institutional participation
• Similar to major market rallies/breakouts

🎯 TRADE RATIONALE:
• Ride the momentum while it's strong
• Exit when RSI starts to cool or ADX weakens
• High probability continuation pattern
• Risk/Reward: {risk_reward:.2f}:1"""

                signal = Signal(
                    timestamp=last['timestamp'],
                    signal_type="LONG",
                    timeframe=timeframe,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    atr=last['atr'],
                    risk_reward=risk_reward,
                    market_bias="bullish",
                    confidence=4,  # High confidence for extreme moves
                    indicators=last.to_dict(),
                    reasoning=reasoning,
                    symbol=symbol,
                    strategy="Extreme RSI Continuation"
                )
                
                return signal
            
            return None
            
        except Exception as e:
            logger.error(f"Error in extreme RSI detection: {e}", exc_info=True)
            return None