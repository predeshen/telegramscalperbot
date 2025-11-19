"""Gold (XAU/USD) Swing Scanner - 15m and 1h timeframes"""
from src.base_scanner import BaseScanner


class GoldSwingScanner(BaseScanner):
    """Gold swing scanner for 15m and 1h timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize Gold swing scanner"""
        asset_config = {
            'min_confluence_factors': 4,
            'min_confidence_score': 3,
            'volume_thresholds': {
                'scalp': 1.4,
                'swing': 1.3,
                'trend_alignment': 0.9,
                'breakout': 1.4,
                'mean_reversion': 1.6,
                'momentum_shift': 1.4
            }
        }
        
        super().__init__(
            scanner_name="Gold Swing Scanner",
            symbol="XAUUSD",
            timeframes=["15m", "1h"],
            config_path=config_path,
            asset_config=asset_config
        )

