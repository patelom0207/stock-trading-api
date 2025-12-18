# Quick Start Guide

Get your Stock Trading API up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Alpha Vantage API key (get free at https://www.alphavantage.co/support/#api-key)

## Setup Steps

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Database

```bash
# Create PostgreSQL database
createdb trading_api

# Or use Docker
docker-compose up -d db
```

### 3. Set Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set:
# - DATABASE_URL=postgresql://user:password@localhost:5432/trading_api
# - ALPHA_VANTAGE_API_KEY=your_key_here
# - SECRET_KEY=any_random_string
```

### 4. Initialize Database

```bash
python -m scripts.init_db
```

### 5. Create Your First User

```bash
python -m scripts.create_user
```

**Save the API key that's displayed!**

### 6. Start the API

```bash
python main.py
```

The API will be running at http://localhost:8000

### 7. Test It Out

Visit http://localhost:8000/docs for the interactive API documentation.

Or try this curl command (replace YOUR_API_KEY):

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "http://localhost:8000/api/price?symbol=AAPL"
```

## Using Docker (Alternative)

If you prefer Docker:

```bash
# Set your API key in .env first
echo "ALPHA_VANTAGE_API_KEY=your_key_here" > .env

# Start everything
docker-compose up -d

# Create a user
docker-compose exec api python -m scripts.create_user
```

## Next Steps

1. **Try the Examples**:
   ```bash
   # Update API key in examples/basic_trading.py
   python examples/basic_trading.py
   ```

2. **Read the Full Documentation**: See [README.md](README.md)

3. **Build Your Strategy**: Check out [examples/ml_backtesting.py](examples/ml_backtesting.py)

## Common Issues

### Database Connection Error

Make sure PostgreSQL is running and DATABASE_URL is correct in `.env`.

### Alpha Vantage Rate Limit

Free tier: 5 calls/minute, 500/day. The API caches data to minimize calls.

### Invalid API Key

Make sure you're using the Bearer token format:
```
Authorization: Bearer YOUR_API_KEY
```

## Need Help?

- API Docs: http://localhost:8000/docs
- Full README: [README.md](README.md)
- Check the examples folder for working code

Happy Trading! 🚀
