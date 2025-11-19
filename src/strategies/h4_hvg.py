"""
H4 HVG (Higher Volume Gap) Strategy
Detects 4-hour timeframe gaps with volume confirmation for gap fill trading.
"""
# This strategy is implemented in src/h4_hvg_detector.py
# Importing for unified access
from src.h4_hvg_detector import H4HVGDetector as H4HVG

__all__ = ['H4HVG']
