"""Multi-Crypto Scanner - Monitors multiple cryptocurrencies"""
from src.base_scanner import BaseScanner


class MultiCryptoScanner(BaseScanner):
    """Multi-crypto scanner for multiple symbols"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize multi-crypto scanner"""
        asset_config = {
            'min_confluence_factors': 4,
            'min_confidence_score': 3,
            'volume_thresholds': {
                'scalp': 1.3,
                'swing': 1.2,
                'trend_alignment': 0.8,
                'breakout': 1.3,
                'mean_reversion': 1.5,
                'momentum_shift': 1.3
            }
        }
        
        super().__init__(
            scanner_name="Multi-Crypto Scanner",
            symbol="MULTI",
            timeframes=["5m", "15m", "1h"],
            config_path=config_path,
            asset_config=asset_config
        )

