from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import pytz

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Trade, Holding, MarketType, TradeSide, PriceCache, HistoricalData
from app.schemas import (
    PriceResponse,
    TradeRequest,
    TradeResponse,
    BalanceResponse,
    HoldingsResponse,
    HoldingItem,
    HistoryResponse,
    Candle,
    MarketStatusResponse,
    UserCreate,
    UserCreateResponse
)
from app.market_data import MarketDataService
from app.config import settings
import secrets

router = APIRouter()


@router.post("/register", response_model=UserCreateResponse, tags=["Authentication"])
async def register_user(
    user_data: UserCreate = None,
    db: Session = Depends(get_db)
):
    """
    Create a new trading account and receive an API key.

    No authentication required - this is how you get your first API key!

    **Optional Parameters:**
    - `balance`: Starting balance (default: $100,000)

    **Returns:**
    - `user_id`: Your unique user ID
    - `api_key`: Your API key for authentication (save this!)
    - `balance`: Your starting balance
    - `message`: Instructions for using your API key

    **Example Response:**
    ```json
    {
        "user_id": 1,
        "api_key": "abc123def456...",
        "balance": 100000.00,
        "message": "Account created! Use this API key in the 'Authorize' button above."
    }
    ```
    """
    try:
        # Generate secure random API key
        api_key = secrets.token_urlsafe(32)

        # Ensure uniqueness
        while db.query(User).filter(User.api_key == api_key).first():
            api_key = secrets.token_urlsafe(32)

        # Set balance
        balance = user_data.balance if user_data and user_data.balance else settings.DEFAULT_BALANCE

        # Create user
        user = User(api_key=api_key, balance=balance)
        db.add(user)
        db.commit()
        db.refresh(user)

        return UserCreateResponse(
            user_id=user.id,
            api_key=api_key,
            balance=user.balance,
            message="Account created successfully! Click the 'Authorize' button at the top of this page and paste your API key to start trading."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


# Resolution mapping for normalization
RESOLUTION_MAP = {
    '1m': '1', '5m': '5', '15m': '15', '30m': '30',
    '1h': '60', '60m': '60',
    '2h': '120', '120m': '120',
    '4h': '240', '240m': '240',
    '1d': 'D', 'd': 'D',
    '1w': 'W', 'w': 'W',
    '1M': 'M', '1mo': 'M', 'm': 'M'
}


def normalize_resolution(resolution: str) -> str:
    """Normalize resolution aliases to canonical keys."""
    return RESOLUTION_MAP.get(resolution, resolution)


@router.get("/price", response_model=PriceResponse)
async def get_price(
    symbol: str = Query(..., description="Ticker symbol (e.g., AAPL, BTC, EURUSD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the current price for a symbol.
    Supports stocks, crypto, and forex.
    """
    try:
        # Check cache first (cache for 1 minute)
        cache_entry = db.query(PriceCache).filter(
            PriceCache.symbol == symbol.upper(),
            PriceCache.cached_at >= datetime.now(pytz.UTC).replace(tzinfo=None) - pytz.timedelta(minutes=1)
        ).first()

        if cache_entry:
            return PriceResponse(
                symbol=cache_entry.symbol,
                market=cache_entry.market,
                price=cache_entry.price,
                source=cache_entry.source,
                updatedAt=int(cache_entry.timestamp.timestamp())
            )

        # Fetch from market data service
        price_data = await MarketDataService.get_price(symbol.upper())

        # Cache the result
        cache = PriceCache(
            symbol=price_data['symbol'],
            market=price_data['market'],
            price=price_data['price'],
            source=price_data['source'],
            timestamp=price_data['timestamp']
        )
        db.add(cache)
        db.commit()

        return PriceResponse(
            symbol=price_data['symbol'],
            market=price_data['market'],
            price=price_data['price'],
            source=price_data['source'],
            updatedAt=int(price_data['timestamp'].timestamp())
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trade", response_model=TradeResponse)
async def execute_trade(
    trade_request: TradeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute a simulated buy/sell trade.
    - Stocks require integer quantities
    - Crypto and forex allow decimal quantities
    - Updates user balance and holdings
    """
    symbol = trade_request.symbol.upper()
    side = trade_request.side
    quantity = trade_request.quantity

    try:
        # Get current price
        price_data = await MarketDataService.get_price(symbol)
        price = price_data['price']
        market = price_data['market']

        # Validate quantity for stocks (must be integer)
        if market == MarketType.STOCK and quantity != int(quantity):
            raise HTTPException(
                status_code=400,
                detail="Stock trades require integer quantities"
            )

        # Calculate transaction fee
        if market == MarketType.STOCK:
            fee = settings.STOCK_TRANSACTION_FEE
        elif market == MarketType.CRYPTO:
            fee = settings.CRYPTO_TRANSACTION_FEE
        else:
            fee = settings.FOREX_TRANSACTION_FEE

        total_cost = quantity * price + fee

        # Check if user has sufficient funds/holdings
        if side == TradeSide.BUY:
            if current_user.balance < total_cost:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient balance. Required: {total_cost}, Available: {current_user.balance}"
                )

            # Deduct from balance
            current_user.balance -= total_cost

            # Update or create holding
            holding = db.query(Holding).filter(
                Holding.user_id == current_user.id,
                Holding.symbol == symbol
            ).first()

            if holding:
                # Update average price
                total_quantity = holding.quantity + quantity
                holding.average_price = (
                    (holding.quantity * holding.average_price) + (quantity * price)
                ) / total_quantity
                holding.quantity = total_quantity
            else:
                holding = Holding(
                    user_id=current_user.id,
                    symbol=symbol,
                    market=market,
                    quantity=quantity,
                    average_price=price
                )
                db.add(holding)

        else:  # SELL
            holding = db.query(Holding).filter(
                Holding.user_id == current_user.id,
                Holding.symbol == symbol
            ).first()

            if not holding or holding.quantity < quantity:
                available = holding.quantity if holding else 0
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient holdings. Required: {quantity}, Available: {available}"
                )

            # Add to balance (subtract fee)
            current_user.balance += (quantity * price - fee)

            # Update holding
            holding.quantity -= quantity
            if holding.quantity == 0:
                db.delete(holding)

        # Record trade
        trade = Trade(
            user_id=current_user.id,
            symbol=symbol,
            market=market,
            side=side,
            quantity=quantity,
            price=price,
            transaction_fee=fee,
            total_cost=total_cost
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        return TradeResponse(
            status="success",
            trade={
                "symbol": symbol,
                "side": side.value,
                "quantity": quantity,
                "price": price,
                "executed_by_uid": str(current_user.id)
            },
            result={
                "trade_id": trade.id,
                "executed_at": trade.executed_at.isoformat(),
                "total_cost": total_cost,
                "transaction_fee": fee,
                "new_balance": current_user.balance
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current cash balance for the authenticated user.
    """
    return BalanceResponse(balance=current_user.balance)


@router.get("/holdings", response_model=HoldingsResponse)
async def get_holdings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all holdings with current prices and P&L calculations.
    """
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()

    holding_items = []
    total_value = 0

    for holding in holdings:
        try:
            # Get current price
            price_data = await MarketDataService.get_price(holding.symbol)
            current_price = price_data['price']

            # Calculate unrealized P&L
            unrealized_pnl = (current_price - holding.average_price) * holding.quantity
            unrealized_pnl_percent = ((current_price - holding.average_price) / holding.average_price) * 100

            position_value = current_price * holding.quantity
            total_value += position_value

            holding_items.append(HoldingItem(
                symbol=holding.symbol,
                market=holding.market,
                quantity=holding.quantity,
                average_price=holding.average_price,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent
            ))
        except Exception as e:
            # If price fetch fails, still include the holding without current price
            holding_items.append(HoldingItem(
                symbol=holding.symbol,
                market=holding.market,
                quantity=holding.quantity,
                average_price=holding.average_price
            ))

    # Calculate realized P&L from trades
    trades = db.query(Trade).filter(Trade.user_id == current_user.id).all()
    realized_pnl = None
    if trades:
        # Simple calculation: current balance - initial balance
        realized_pnl = current_user.balance - settings.DEFAULT_BALANCE

    total_portfolio_value = current_user.balance + total_value

    return HoldingsResponse(
        holdings=holding_items,
        total_value=total_value,
        cash_balance=current_user.balance,
        total_portfolio_value=total_portfolio_value,
        realized_pnl=realized_pnl
    )


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    symbol: str = Query(..., description="Ticker symbol"),
    resolution: str = Query(..., description="Resolution (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M)"),
    limit: int = Query(500, ge=1, le=5000, description="Number of candles to return"),
    start_ts: Optional[int] = Query(None, description="Start timestamp (Unix seconds, inclusive)"),
    end_ts: Optional[int] = Query(None, description="End timestamp (Unix seconds, exclusive)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch historical OHLCV data for a symbol.
    Supports multiple resolutions and time ranges.
    """
    try:
        # Normalize resolution
        canonical_resolution = normalize_resolution(resolution)
        symbol = symbol.upper()

        # Detect market
        market = MarketDataService.detect_market(symbol)

        # Check cache first
        query = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.resolution == canonical_resolution
        )

        if start_ts:
            start_dt = datetime.fromtimestamp(start_ts, tz=pytz.UTC)
            query = query.filter(HistoricalData.timestamp >= start_dt)

        if end_ts:
            end_dt = datetime.fromtimestamp(end_ts, tz=pytz.UTC)
            query = query.filter(HistoricalData.timestamp < end_dt)

        cached_data = query.order_by(HistoricalData.timestamp.desc()).limit(limit).all()

        # If we have enough cached data, return it
        if len(cached_data) >= limit:
            candles = [
                Candle(
                    timestamp=int(candle.timestamp.timestamp()),
                    open=candle.open,
                    high=candle.high,
                    low=candle.low,
                    close=candle.close,
                    volume=candle.volume
                )
                for candle in reversed(cached_data)
            ]

            return HistoryResponse(
                symbol=symbol,
                market=market,
                resolution=resolution,
                count=len(candles),
                history=candles,
                source="cache",
                updatedAt=int(datetime.now(pytz.UTC).timestamp())
            )

        # Fetch from market data service
        history_data = await MarketDataService.get_historical_data(
            symbol=symbol,
            resolution=canonical_resolution,
            limit=limit,
            market=market
        )

        # Cache the results
        for candle_data in history_data:
            candle_dt = datetime.fromtimestamp(candle_data['timestamp'], tz=pytz.UTC)

            # Check if already exists
            existing = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.resolution == canonical_resolution,
                HistoricalData.timestamp == candle_dt
            ).first()

            if not existing:
                historical_data = HistoricalData(
                    symbol=symbol,
                    market=market,
                    resolution=canonical_resolution,
                    timestamp=candle_dt,
                    open=candle_data['open'],
                    high=candle_data['high'],
                    low=candle_data['low'],
                    close=candle_data['close'],
                    volume=candle_data['volume'],
                    source='alpha_vantage'
                )
                db.add(historical_data)

        db.commit()

        candles = [Candle(**candle_data) for candle_data in history_data]

        return HistoryResponse(
            symbol=symbol,
            market=market,
            resolution=resolution,
            count=len(candles),
            history=candles,
            source="alpha_vantage",
            updatedAt=int(datetime.now(pytz.UTC).timestamp())
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/market_status", response_model=MarketStatusResponse)
async def get_market_status(
    symbol: Optional[str] = Query(None, description="Ticker symbol"),
    market: Optional[str] = Query(None, description="Market type (stock, crypto, forex)"),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a market is currently open for trading.
    If symbol is provided, it determines the market type.
    """
    try:
        if symbol:
            market_type = MarketDataService.detect_market(symbol.upper())
        elif market:
            market_type = MarketType(market.lower())
        else:
            raise HTTPException(
                status_code=400,
                detail="Either 'symbol' or 'market' parameter is required"
            )

        is_open = MarketDataService.is_market_open(market_type)

        return MarketStatusResponse(isOpen=is_open)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
