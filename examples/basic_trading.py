"""
Basic trading example demonstrating API usage.
"""
import requests
import time

# Configuration
BASE_URL = "http://localhost:8000/api"
API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key

headers = {"Authorization": f"Bearer {API_KEY}"}


def get_price(symbol: str):
    """Fetch current price for a symbol."""
    response = requests.get(f"{BASE_URL}/price", params={"symbol": symbol}, headers=headers)
    response.raise_for_status()
    return response.json()


def execute_trade(symbol: str, side: str, quantity: float):
    """Execute a buy or sell trade."""
    trade_data = {"symbol": symbol, "side": side, "quantity": quantity}
    response = requests.post(f"{BASE_URL}/trade", json=trade_data, headers=headers)
    response.raise_for_status()
    return response.json()


def get_balance():
    """Get current cash balance."""
    response = requests.get(f"{BASE_URL}/balance", headers=headers)
    response.raise_for_status()
    return response.json()


def get_holdings():
    """Get all holdings with P&L."""
    response = requests.get(f"{BASE_URL}/holdings", headers=headers)
    response.raise_for_status()
    return response.json()


def get_history(symbol: str, resolution: str = "1d", limit: int = 30):
    """Get historical OHLCV data."""
    params = {"symbol": symbol, "resolution": resolution, "limit": limit}
    response = requests.get(f"{BASE_URL}/history", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    """Demonstrate basic trading operations."""
    print("🚀 Stock Trading API - Basic Example\n")

    # 1. Check initial balance
    print("1. Checking initial balance...")
    balance = get_balance()
    print(f"   Cash Balance: ${balance['balance']:,.2f}\n")

    # 2. Get current price
    symbol = "AAPL"
    print(f"2. Fetching current price for {symbol}...")
    price_data = get_price(symbol)
    print(f"   {price_data['symbol']}: ${price_data['price']:.2f}")
    print(f"   Market: {price_data['market']}")
    print(f"   Source: {price_data['source']}\n")

    # 3. Execute a buy trade
    quantity = 10
    print(f"3. Buying {quantity} shares of {symbol}...")
    trade = execute_trade(symbol, "buy", quantity)
    print(f"   ✅ Trade executed successfully!")
    print(f"   Price: ${trade['trade']['price']:.2f}")
    print(f"   Total Cost: ${trade['result']['total_cost']:.2f}")
    print(f"   New Balance: ${trade['result']['new_balance']:,.2f}\n")

    # 4. Check holdings
    print("4. Checking portfolio...")
    holdings = get_holdings()
    print(f"   Cash: ${holdings['cash_balance']:,.2f}")
    print(f"   Holdings Value: ${holdings['total_value']:,.2f}")
    print(f"   Total Portfolio: ${holdings['total_portfolio_value']:,.2f}")
    print(f"\n   Individual Holdings:")
    for holding in holdings['holdings']:
        print(f"   - {holding['symbol']}: {holding['quantity']} shares @ ${holding['average_price']:.2f}")
        if holding.get('unrealized_pnl') is not None:
            pnl = holding['unrealized_pnl']
            pnl_pct = holding['unrealized_pnl_percent']
            print(f"     Current: ${holding['current_price']:.2f} | P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
    print()

    # 5. Get historical data
    print(f"5. Fetching historical data for {symbol}...")
    history = get_history(symbol, resolution="1d", limit=5)
    print(f"   Last 5 days of {history['symbol']}:")
    for candle in history['history'][-5:]:
        print(f"   - Close: ${candle['close']:.2f} | Volume: {candle['volume']:,.0f}")
    print()

    # 6. Execute a sell trade
    sell_quantity = 5
    print(f"6. Selling {sell_quantity} shares of {symbol}...")
    trade = execute_trade(symbol, "sell", sell_quantity)
    print(f"   ✅ Trade executed successfully!")
    print(f"   Price: ${trade['trade']['price']:.2f}")
    print(f"   Total Received: ${trade['result']['total_cost']:.2f}")
    print(f"   New Balance: ${trade['result']['new_balance']:,.2f}\n")

    # 7. Final portfolio check
    print("7. Final portfolio status...")
    holdings = get_holdings()
    print(f"   Total Portfolio Value: ${holdings['total_portfolio_value']:,.2f}")
    if holdings.get('realized_pnl') is not None:
        print(f"   Realized P&L: ${holdings['realized_pnl']:+,.2f}")
    print()

    print("✨ Example completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
