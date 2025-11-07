#!/usr/bin/env python3
"""Create clean signal_detector.py file."""

code = '''"""Signal detection with confluence-based trading logic."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict
import pandas as pd
import logging

from src.trend_analyzer import TrendAnalyzer


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
    strategy: str = ""  # Strategy name (e.g., "Trend Following", "EMA Crossover")
    trend_direction: Optional[str] = None  # "uptrend" or "downtrend" for trend signals
    swing_points: Optional[int] = None  # Number of swing highs/lows for trend signals
    pullback_depth: Optional[float] = None  # Pullback percentage for trend signals
    
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
'''

# Write in chunks to avoid issues
with open('src/signal_detector.py', 'w', encoding='utf-8', newline='\n') as f:
    f.write(code)

print("Part 1 written")
