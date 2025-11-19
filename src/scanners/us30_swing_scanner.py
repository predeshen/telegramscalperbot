"""US30 (Dow Jones) Swing Scanner - 15m and 1h timeframes"""
from src.base_scanner import BaseScanner


class US30SwingScanner(BaseScanner):
    """US30 swing scanner for 15m and 1h timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize US30 swing scanner"""
        asset_config = {
            'min_confluence_factors': 4,
            'min_confidence_score': 3,
            'volume_thresholds': {
                'momentum': 1.5,
                'trend_alignment': 1.0,
                'breakout': 1.5,
                'mean_reversion': 1.6,
                'momentum_shift': 1.5
            }
        }
        
        super().__init__(
            scanner_name="US30 Swing Scanner",
            symbol="US30",
            timeframes=["15m", "1h"],
            config_path=config_path,
            asset_config=asset_config
        )

