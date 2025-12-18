from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base


class MarketType(str, enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"


class TradeSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String, unique=True, index=True, nullable=False)
    balance = Column(Float, default=100000.00, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    market = Column(Enum(MarketType), nullable=False)
    side = Column(Enum(TradeSide), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    transaction_fee = Column(Float, default=0.0)
    total_cost = Column(Float, nullable=False)  # quantity * price + fee
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="trades")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_user_symbol', 'user_id', 'symbol'),
        Index('idx_user_executed', 'user_id', 'executed_at'),
    )


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, nullable=False)
    market = Column(Enum(MarketType), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)  # For P&L calculation
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="holdings")

    # Unique constraint: one holding per user per symbol
    __table_args__ = (
        Index('idx_user_symbol_unique', 'user_id', 'symbol', unique=True),
    )


class PriceCache(Base):
    """Cache for price data to reduce API calls."""
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    market = Column(Enum(MarketType), nullable=False)
    price = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


class HistoricalData(Base):
    """Store OHLCV historical data."""
    __tablename__ = "historical_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    market = Column(Enum(MarketType), nullable=False)
    resolution = Column(String, nullable=False)  # 1m, 5m, 1h, 1d, etc.
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_symbol_resolution_timestamp', 'symbol', 'resolution', 'timestamp', unique=True),
    )
