import httpx
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pytz
from app.config import settings
from app.models import MarketType


class MarketDataService:
    """Service for fetching market data from Alpha Vantage."""

    BASE_URL = "https://www.alphavantage.co/query"

    # Symbol detection patterns
    CRYPTO_SYMBOLS = ['BTC', 'ETH', 'USDT', 'BNB', 'XRP', 'ADA', 'DOGE', 'SOL', 'TRX', 'DOT']
    FOREX_PAIRS = ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD', 'CNY']

    @classmethod
    def detect_market(cls, symbol: str) -> MarketType:
        """Detect market type from symbol."""
        symbol_upper = symbol.upper()

        # Check if it's a known crypto
        if symbol_upper in cls.CRYPTO_SYMBOLS:
            return MarketType.CRYPTO

        # Check if it's a forex pair (typically 6 characters like EURUSD)
        if len(symbol_upper) == 6 and symbol_upper[:3] in cls.FOREX_PAIRS:
            return MarketType.FOREX

        # Default to stock
        return MarketType.STOCK

    @classmethod
    async def get_price(cls, symbol: str, market: Optional[MarketType] = None) -> Dict:
        """
        Fetch current price for a symbol.

        Args:
            symbol: The ticker symbol
            market: Market type (auto-detected if not provided)

        Returns:
            Dict with price, market, source, and timestamp
        """
        if market is None:
            market = cls.detect_market(symbol)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if market == MarketType.CRYPTO:
                return await cls._get_crypto_price(client, symbol)
            elif market == MarketType.FOREX:
                return await cls._get_forex_price(client, symbol)
            else:
                return await cls._get_stock_price(client, symbol)

    @classmethod
    async def _get_stock_price(cls, client: httpx.AsyncClient, symbol: str) -> Dict:
        """Fetch stock price from Alpha Vantage."""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': settings.ALPHA_VANTAGE_API_KEY
        }

        response = await client.get(cls.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'Global Quote' not in data or not data['Global Quote']:
            raise ValueError(f"No data found for symbol {symbol}")

        quote = data['Global Quote']
        price = float(quote.get('05. price', 0))

        return {
            'symbol': symbol,
            'market': MarketType.STOCK,
            'price': price,
            'source': 'alpha_vantage',
            'timestamp': datetime.now(pytz.UTC)
        }

    @classmethod
    async def _get_crypto_price(cls, client: httpx.AsyncClient, symbol: str) -> Dict:
        """Fetch crypto price from Alpha Vantage."""
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': symbol,
            'to_currency': 'USD',
            'apikey': settings.ALPHA_VANTAGE_API_KEY
        }

        response = await client.get(cls.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'Realtime Currency Exchange Rate' not in data:
            raise ValueError(f"No data found for crypto {symbol}")

        rate = data['Realtime Currency Exchange Rate']
        price = float(rate.get('5. Exchange Rate', 0))

        return {
            'symbol': symbol,
            'market': MarketType.CRYPTO,
            'price': price,
            'source': 'alpha_vantage',
            'timestamp': datetime.now(pytz.UTC)
        }

    @classmethod
    async def _get_forex_price(cls, client: httpx.AsyncClient, symbol: str) -> Dict:
        """Fetch forex price from Alpha Vantage."""
        # Symbol should be like EURUSD - split to from/to
        from_currency = symbol[:3]
        to_currency = symbol[3:6]

        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency,
            'apikey': settings.ALPHA_VANTAGE_API_KEY
        }

        response = await client.get(cls.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'Realtime Currency Exchange Rate' not in data:
            raise ValueError(f"No data found for forex {symbol}")

        rate = data['Realtime Currency Exchange Rate']
        price = float(rate.get('5. Exchange Rate', 0))

        return {
            'symbol': symbol,
            'market': MarketType.FOREX,
            'price': price,
            'source': 'alpha_vantage',
            'timestamp': datetime.now(pytz.UTC)
        }

    @classmethod
    async def get_historical_data(
        cls,
        symbol: str,
        resolution: str,
        limit: int = 500,
        market: Optional[MarketType] = None
    ) -> List[Dict]:
        """
        Fetch historical OHLCV data.

        Args:
            symbol: The ticker symbol
            resolution: Time resolution (1, 5, 15, 30, 60, D, W, M)
            limit: Number of candles to return
            market: Market type (auto-detected if not provided)

        Returns:
            List of candle dictionaries
        """
        if market is None:
            market = cls.detect_market(symbol)

        async with httpx.AsyncClient(timeout=30.0) as client:
            if market == MarketType.STOCK:
                return await cls._get_stock_history(client, symbol, resolution, limit)
            elif market == MarketType.CRYPTO:
                return await cls._get_crypto_history(client, symbol, resolution, limit)
            else:
                return await cls._get_forex_history(client, symbol, resolution, limit)

    @classmethod
    async def _get_stock_history(
        cls,
        client: httpx.AsyncClient,
        symbol: str,
        resolution: str,
        limit: int
    ) -> List[Dict]:
        """Fetch stock historical data."""
        # Map resolution to Alpha Vantage function
        if resolution in ['1', '5', '15', '30', '60']:
            function = 'TIME_SERIES_INTRADAY'
            interval = f"{resolution}min"
            params = {
                'function': function,
                'symbol': symbol,
                'interval': interval,
                'apikey': settings.ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'
            }
            time_series_key = f'Time Series ({interval})'
        elif resolution == 'D':
            function = 'TIME_SERIES_DAILY'
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': settings.ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'
            }
            time_series_key = 'Time Series (Daily)'
        elif resolution == 'W':
            function = 'TIME_SERIES_WEEKLY'
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': settings.ALPHA_VANTAGE_API_KEY
            }
            time_series_key = 'Weekly Time Series'
        elif resolution == 'M':
            function = 'TIME_SERIES_MONTHLY'
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': settings.ALPHA_VANTAGE_API_KEY
            }
            time_series_key = 'Monthly Time Series'
        else:
            raise ValueError(f"Unsupported resolution: {resolution}")

        response = await client.get(cls.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if time_series_key not in data:
            raise ValueError(f"No historical data found for {symbol}")

        time_series = data[time_series_key]

        # Convert to list of candles
        candles = []
        for timestamp_str, values in sorted(time_series.items(), reverse=True)[:limit]:
            timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
            if timestamp.tzinfo is None:
                timestamp = pytz.UTC.localize(timestamp)

            candles.append({
                'timestamp': int(timestamp.timestamp()),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': float(values['5. volume'])
            })

        return list(reversed(candles))  # Return in chronological order

    @classmethod
    async def _get_crypto_history(
        cls,
        client: httpx.AsyncClient,
        symbol: str,
        resolution: str,
        limit: int
    ) -> List[Dict]:
        """Fetch crypto historical data."""
        # Alpha Vantage has limited intraday crypto support
        # For now, use daily data
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': symbol,
            'market': 'USD',
            'apikey': settings.ALPHA_VANTAGE_API_KEY
        }

        response = await client.get(cls.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        time_series_key = 'Time Series (Digital Currency Daily)'
        if time_series_key not in data:
            raise ValueError(f"No historical data found for {symbol}")

        time_series = data[time_series_key]

        candles = []
        for timestamp_str, values in sorted(time_series.items(), reverse=True)[:limit]:
            timestamp = datetime.fromisoformat(timestamp_str)
            if timestamp.tzinfo is None:
                timestamp = pytz.UTC.localize(timestamp)

            candles.append({
                'timestamp': int(timestamp.timestamp()),
                'open': float(values['1a. open (USD)']),
                'high': float(values['2a. high (USD)']),
                'low': float(values['3a. low (USD)']),
                'close': float(values['4a. close (USD)']),
                'volume': float(values['5. volume'])
            })

        return list(reversed(candles))

    @classmethod
    async def _get_forex_history(
        cls,
        client: httpx.AsyncClient,
        symbol: str,
        resolution: str,
        limit: int
    ) -> List[Dict]:
        """Fetch forex historical data."""
        from_currency = symbol[:3]
        to_currency = symbol[3:6]

        # Map resolution to function
        if resolution in ['1', '5', '15', '30', '60']:
            function = 'FX_INTRADAY'
            interval = f"{resolution}min"
            params = {
                'function': function,
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'interval': interval,
                'apikey': settings.ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'
            }
            time_series_key = f'Time Series FX (Intraday)'
        else:
            function = 'FX_DAILY'
            params = {
                'function': function,
                'from_symbol': from_currency,
                'to_symbol': to_currency,
                'apikey': settings.ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'
            }
            time_series_key = 'Time Series FX (Daily)'

        response = await client.get(cls.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if time_series_key not in data:
            raise ValueError(f"No historical data found for {symbol}")

        time_series = data[time_series_key]

        candles = []
        for timestamp_str, values in sorted(time_series.items(), reverse=True)[:limit]:
            timestamp = datetime.fromisoformat(timestamp_str.replace(' ', 'T'))
            if timestamp.tzinfo is None:
                timestamp = pytz.UTC.localize(timestamp)

            candles.append({
                'timestamp': int(timestamp.timestamp()),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': 0  # Forex doesn't have volume in Alpha Vantage
            })

        return list(reversed(candles))

    @classmethod
    def is_market_open(cls, market: MarketType) -> bool:
        """
        Check if market is currently open for trading.

        Note: This is a simplified implementation.
        For production, consider holidays and exact trading hours.
        """
        now = datetime.now(pytz.timezone('US/Eastern'))

        if market == MarketType.CRYPTO:
            # Crypto markets are always open
            return True
        elif market == MarketType.FOREX:
            # Forex is open 24/5 (closed weekends)
            return now.weekday() < 5
        else:  # STOCK
            # US stock market: Mon-Fri, 9:30 AM - 4:00 PM ET
            if now.weekday() >= 5:  # Weekend
                return False

            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

            return market_open <= now <= market_close
