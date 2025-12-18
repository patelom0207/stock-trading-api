# Stock Trading API

A simulated stock trading API built with FastAPI that uses real market data from Alpha Vantage. Perfect for training algorithmic trading models and backtesting trading strategies.

## Features

- **Multi-Asset Support**: Trade stocks, cryptocurrencies, and forex
- **Real Market Data**: Powered by Alpha Vantage API
- **Simulated Trading**: Execute buy/sell orders without real money
- **Portfolio Management**: Track holdings, balance, and P&L
- **Historical Data**: OHLCV data with multiple time resolutions
- **Market Hours**: Realistic trading windows for different asset classes
- **API Key Authentication**: Secure Bearer token authentication
- **Database Caching**: Efficient data caching to minimize API calls

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Market Data**: Alpha Vantage API
- **Authentication**: Bearer Token (API Keys)

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Alpha Vantage API Key (free at https://www.alphavantage.co/support/#api-key)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd stock-trading-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a PostgreSQL database:
```bash
createdb trading_api
```

5. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL`: Your PostgreSQL connection string
- `ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key
- `SECRET_KEY`: A secure random string

6. Initialize the database:
```bash
python -m scripts.init_db
```

7. Create a user and get an API key:
```bash
python -m scripts.create_user
```

Save the API key provided - you'll need it for authentication!

## Running the API

### Development Mode

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

All endpoints require authentication via Bearer token:
```
Authorization: Bearer YOUR_API_KEY
```

### GET /api/price

Fetch the current price for a symbol.

**Parameters:**
- `symbol` (required): Ticker symbol (e.g., AAPL, BTC, EURUSD)

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/price?symbol=AAPL"
```

**Response:**
```json
{
  "symbol": "AAPL",
  "market": "stock",
  "price": 178.50,
  "source": "alpha_vantage",
  "updatedAt": 1712345678
}
```

### POST /api/trade

Execute a simulated buy or sell trade.

**Request Body:**
```json
{
  "symbol": "AAPL",
  "side": "buy",
  "quantity": 10
}
```

**Notes:**
- Stocks require integer quantities
- Crypto and forex allow decimal quantities
- Validates sufficient balance/holdings

**Example:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","side":"buy","quantity":10}' \
  "http://localhost:8000/api/trade"
```

**Response:**
```json
{
  "status": "success",
  "trade": {
    "symbol": "AAPL",
    "side": "buy",
    "quantity": 10,
    "price": 178.50,
    "executed_by_uid": "1"
  },
  "result": {
    "trade_id": 1,
    "executed_at": "2024-01-15T10:30:00Z",
    "total_cost": 1785.00,
    "transaction_fee": 0.0,
    "new_balance": 98215.00
  }
}
```

### GET /api/balance

Get current cash balance.

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/balance"
```

**Response:**
```json
{
  "balance": 98215.00
}
```

### GET /api/holdings

Get all holdings with current prices and P&L.

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/holdings"
```

**Response:**
```json
{
  "holdings": [
    {
      "symbol": "AAPL",
      "market": "stock",
      "quantity": 10,
      "average_price": 178.50,
      "current_price": 180.25,
      "unrealized_pnl": 17.50,
      "unrealized_pnl_percent": 0.98
    }
  ],
  "total_value": 1802.50,
  "cash_balance": 98215.00,
  "total_portfolio_value": 100017.50,
  "realized_pnl": 17.50
}
```

### GET /api/history

Fetch historical OHLCV data.

**Parameters:**
- `symbol` (required): Ticker symbol
- `resolution` (required): Time resolution
  - Supported: `1m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `1d`, `1w`, `1M`
- `limit` (optional): Number of candles (1-5000, default: 500)
- `start_ts` (optional): Start timestamp (Unix seconds)
- `end_ts` (optional): End timestamp (Unix seconds)

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/history?symbol=AAPL&resolution=1d&limit=30"
```

**Response:**
```json
{
  "symbol": "AAPL",
  "market": "stock",
  "resolution": "1d",
  "count": 30,
  "history": [
    {
      "timestamp": 1712345678,
      "open": 175.00,
      "high": 180.50,
      "low": 174.20,
      "close": 178.50,
      "volume": 50000000
    }
  ],
  "source": "alpha_vantage",
  "updatedAt": 1712349999
}
```

### GET /api/market_status

Check if a market is currently open.

**Parameters:**
- `symbol` (optional): Ticker symbol
- `market` (optional): Market type (stock, crypto, forex)

**Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/market_status?symbol=AAPL"
```

**Response:**
```json
{
  "isOpen": true
}
```

## Market Types

The API automatically detects market types:

- **Stocks**: Standard ticker symbols (AAPL, MSFT, GOOGL)
- **Crypto**: Common crypto symbols (BTC, ETH, USDT)
- **Forex**: 6-character pairs (EURUSD, GBPJPY)

## Resolution Mapping

Historical data supports multiple resolution formats:

| Input | Canonical | Description |
|-------|-----------|-------------|
| 1m, 1 | 1 | 1 minute |
| 5m, 5 | 5 | 5 minutes |
| 15m, 15 | 15 | 15 minutes |
| 30m, 30 | 30 | 30 minutes |
| 1h, 60m, 60 | 60 | 1 hour |
| 2h, 120m, 120 | 120 | 2 hours |
| 4h, 240m, 240 | 240 | 4 hours |
| 1d, d, D | D | Daily |
| 1w, w, W | W | Weekly |
| 1M, m, M | M | Monthly |

## Utility Scripts

### Create a New User

```bash
python -m scripts.create_user --balance 100000
```

### Initialize Database

```bash
python -m scripts.init_db
```

### Reset User Account

```bash
python -m scripts.reset_user <API_KEY>
```

This clears all trades and holdings and resets balance to default.

## Trading Rules

1. **Stocks**:
   - Integer quantities only
   - Market hours: Mon-Fri, 9:30 AM - 4:00 PM ET
   - No trading on weekends

2. **Crypto**:
   - Decimal quantities allowed
   - 24/7 trading

3. **Forex**:
   - Decimal quantities allowed
   - 24/5 trading (closed weekends)

## Using with Algorithmic Trading

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api"
API_KEY = "your_api_key_here"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Get current price
response = requests.get(f"{BASE_URL}/price?symbol=AAPL", headers=headers)
price_data = response.json()
print(f"AAPL Price: ${price_data['price']}")

# Execute a buy order
trade_data = {
    "symbol": "AAPL",
    "side": "buy",
    "quantity": 10
}
response = requests.post(f"{BASE_URL}/trade", json=trade_data, headers=headers)
trade_result = response.json()
print(f"Trade executed: {trade_result}")

# Get historical data for backtesting
response = requests.get(
    f"{BASE_URL}/history?symbol=AAPL&resolution=1d&limit=100",
    headers=headers
)
history = response.json()
candles = history['history']

# Check portfolio
response = requests.get(f"{BASE_URL}/holdings", headers=headers)
portfolio = response.json()
print(f"Portfolio Value: ${portfolio['total_portfolio_value']}")
```

### Training ML Models

The API is ideal for:
- **Backtesting**: Use historical data to test strategies
- **Reinforcement Learning**: Train agents with simulated trading
- **Feature Engineering**: Access OHLCV data for technical indicators
- **Paper Trading**: Test live strategies without risk

## Rate Limiting

Alpha Vantage free tier allows:
- 5 API calls per minute
- 500 calls per day

The API implements caching to minimize external calls:
- Price data cached for 1 minute
- Historical data cached indefinitely

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (validation errors)
- `401`: Unauthorized (invalid API key)
- `500`: Server error

## Development

### Run Tests

```bash
pytest
```

### Code Style

```bash
black .
flake8 .
```

## License

MIT License - feel free to use for your trading bots and ML experiments!

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review this README
3. Open an issue on GitHub

## Disclaimer

This is a simulated trading API for educational and development purposes only. It uses real market data but executes only simulated trades. Not for actual financial trading.
