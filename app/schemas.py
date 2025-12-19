from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MarketType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"


class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Resolution(str, Enum):
    # Canonical keys (what we store internally)
    ONE_MIN = "1"
    FIVE_MIN = "5"
    FIFTEEN_MIN = "15"
    THIRTY_MIN = "30"
    SIXTY_MIN = "60"
    ONE_TWENTY_MIN = "120"
    TWO_FORTY_MIN = "240"
    DAILY = "D"
    WEEKLY = "W"
    MONTHLY = "M"


# Request/Response Schemas

class PriceResponse(BaseModel):
    symbol: str
    market: MarketType
    price: float
    source: str
    updatedAt: int  # Unix timestamp

    class Config:
        from_attributes = True


class TradeRequest(BaseModel):
    symbol: str
    side: TradeSide
    quantity: float = Field(gt=0)

    @validator('quantity')
    def validate_quantity(cls, v, values):
        return v


class TradeResponse(BaseModel):
    status: str
    trade: dict
    result: dict


class BalanceResponse(BaseModel):
    balance: float


class HoldingItem(BaseModel):
    symbol: str
    market: MarketType
    quantity: float
    average_price: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None


class HoldingsResponse(BaseModel):
    holdings: List[HoldingItem]
    total_value: float
    cash_balance: float
    total_portfolio_value: float
    realized_pnl: Optional[float] = None


class Candle(BaseModel):
    timestamp: int  # Unix timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoryResponse(BaseModel):
    symbol: str
    market: MarketType
    resolution: str
    count: int
    history: List[Candle]
    source: str
    updatedAt: int  # Unix timestamp


class MarketStatusResponse(BaseModel):
    isOpen: bool


class UserCreate(BaseModel):
    balance: Optional[float] = None


class UserCreateResponse(BaseModel):
    user_id: int
    api_key: str
    balance: float
    message: str
