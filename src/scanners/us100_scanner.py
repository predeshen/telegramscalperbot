"""US100 (Nasdaq 100) Scanner - 5m and 15m timeframes"""
from src.base_scanner import BaseScanner


class US100Scanner(BaseScanner):
    """US100 scanner for 5m and 15m timeframes"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize US100 scanner"""
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
            scanner_name="US100 Scanner",
            symbol="US100",
            timeframes=["5m", "15m"],
            config_path=config_path,
            asset_config=asset_config
        )

