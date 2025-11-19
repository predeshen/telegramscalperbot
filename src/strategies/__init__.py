"""
Unified Strategy Implementations
All trading strategies consolidated into a single module for easy management and reuse.
"""

try:
    from src.strategies.fibonacci_retracement import FibonacciRetracement
except ImportError:
    FibonacciRetracement = None

try:
    from src.strategies.h4_hvg import H4HVG
except ImportError:
    H4HVG = None

try:
    from src.strategies.support_resistance import SupportResistance
except ImportError:
    SupportResistance = None

try:
    from src.strategies.ema_crossover import EMACrossover
except ImportError:
    EMACrossover = None

try:
    from src.strategies.momentum_shift import MomentumShift
except ImportError:
    MomentumShift = None

try:
    from src.strategies.trend_alignment import TrendAlignment
except ImportError:
    TrendAlignment = None

try:
    from src.strategies.mean_reversion import MeanReversion
except ImportError:
    MeanReversion = None

__all__ = [
    'FibonacciRetracement',
    'H4HVG',
    'SupportResistance',
    'EMACrossover',
    'MomentumShift',
    'TrendAlignment',
    'MeanReversion'
]
