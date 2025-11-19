"""
Symbol Context Management
Ensures symbol information is properly propagated through the entire signal pipeline
"""
import logging
from dataclasses import dataclass
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class SymbolContext:
    """
    Manages symbol context throughout signal pipeline
    """
    symbol: str  # Internal symbol (BTC, XAUUSD, US30)
    display_name: str  # Display name for alerts
    asset_type: str  # crypto, commodity, index
    yf_symbol: Optional[str] = None  # Yahoo Finance symbol
    emoji: Optional[str] = None  # Asset-specific emoji
    
    def __post_init__(self):
        """Initialize emoji and validate symbol"""
        if self.emoji is None:
            self.emoji = self._get_emoji()
        
        if not self.validate():
            raise ValueError(f"Invalid symbol context: symbol='{self.symbol}'")
    
    def _get_emoji(self) -> str:
        """Get asset-specific emoji for alerts"""
        emoji_map = {
            "BTC": "₿",
            "XAUUSD": "🥇",
            "US30": "📊",
            "US100": "💹"
        }
        return emoji_map.get(self.symbol, "📈")
    
    def validate(self) -> bool:
        """Ensure symbol is not null or empty"""
        if not self.symbol or not self.symbol.strip():
            logger.error("Symbol context validation failed: symbol is null or empty")
            return False
        
        if not self.display_name or not self.display_name.strip():
            logger.error("Symbol context validation failed: display_name is null or empty")
            return False
        
        if not self.asset_type or not self.asset_type.strip():
            logger.error("Symbol context validation failed: asset_type is null or empty")
            return False
        
        return True
    
    def get_formatted_name(self) -> str:
        """Get formatted name with emoji"""
        return f"{self.emoji} {self.display_name}"
    
    @classmethod
    def from_symbol(cls, symbol: str) -> 'SymbolContext':
        """
        Create SymbolContext from internal symbol
        
        Args:
            symbol: Internal symbol (BTC, XAUUSD, US30)
            
        Returns:
            SymbolContext instance
            
        Raises:
            ValueError: If symbol is unknown
        """
        symbol_configs = {
            "BTC": {
                "display_name": "BTC/USD",
                "asset_type": "crypto",
                "yf_symbol": "BTC-USD"
            },
            "XAUUSD": {
                "display_name": "XAU/USD",
                "asset_type": "commodity",
                "yf_symbol": "GC=F"
            },
            "US30": {
                "display_name": "US30",
                "asset_type": "index",
                "yf_symbol": "^DJI"
            },
            "US100": {
                "display_name": "US100/NASDAQ",
                "asset_type": "index",
                "yf_symbol": "^IXIC"
            }
        }
        
        if symbol not in symbol_configs:
            raise ValueError(f"Unknown symbol: {symbol}. Available: {list(symbol_configs.keys())}")
        
        config = symbol_configs[symbol]
        
        return cls(
            symbol=symbol,
            display_name=config["display_name"],
            asset_type=config["asset_type"],
            yf_symbol=config["yf_symbol"]
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "display_name": self.display_name,
            "asset_type": self.asset_type,
            "yf_symbol": self.yf_symbol,
            "emoji": self.emoji
        }
