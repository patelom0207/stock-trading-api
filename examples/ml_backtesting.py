"""
Example of using the API for backtesting a simple moving average crossover strategy.
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api"
API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual API key

headers = {"Authorization": f"Bearer {API_KEY}"}


def get_historical_data(symbol: str, resolution: str = "1d", limit: int = 200):
    """Fetch historical OHLCV data."""
    params = {"symbol": symbol, "resolution": resolution, "limit": limit}
    response = requests.get(f"{BASE_URL}/history", params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data['history'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)

    return df


def calculate_sma(df: pd.DataFrame, window: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return df['close'].rolling(window=window).mean()


def moving_average_crossover_strategy(df: pd.DataFrame, short_window: int = 20, long_window: int = 50):
    """
    Simple Moving Average Crossover Strategy.

    Buy signal: Short MA crosses above Long MA
    Sell signal: Short MA crosses below Long MA
    """
    # Calculate moving averages
    df['SMA_short'] = calculate_sma(df, short_window)
    df['SMA_long'] = calculate_sma(df, long_window)

    # Generate signals
    df['signal'] = 0
    df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1  # Buy signal
    df.loc[df['SMA_short'] < df['SMA_long'], 'signal'] = -1  # Sell signal

    # Identify crossovers
    df['position'] = df['signal'].diff()

    return df


def backtest_strategy(symbol: str, initial_balance: float = 100000):
    """
    Backtest the moving average crossover strategy.
    """
    print(f"📊 Backtesting Strategy for {symbol}\n")
    print(f"Initial Balance: ${initial_balance:,.2f}")
    print(f"Strategy: Moving Average Crossover (20/50)\n")

    # Fetch historical data
    print("Fetching historical data...")
    df = get_historical_data(symbol, resolution="1d", limit=200)
    print(f"Loaded {len(df)} candles\n")

    # Apply strategy
    df = moving_average_crossover_strategy(df)

    # Simulate trading
    cash = initial_balance
    shares = 0
    trades = []

    for idx, row in df.iterrows():
        # Buy signal (crossover up)
        if row['position'] == 2 and cash > 0:
            # Buy as many shares as possible
            shares_to_buy = int(cash / row['close'])
            if shares_to_buy > 0:
                cost = shares_to_buy * row['close']
                cash -= cost
                shares += shares_to_buy
                trades.append({
                    'date': idx,
                    'action': 'BUY',
                    'shares': shares_to_buy,
                    'price': row['close'],
                    'total': cost
                })

        # Sell signal (crossover down)
        elif row['position'] == -2 and shares > 0:
            # Sell all shares
            revenue = shares * row['close']
            cash += revenue
            trades.append({
                'date': idx,
                'action': 'SELL',
                'shares': shares,
                'price': row['close'],
                'total': revenue
            })
            shares = 0

    # Final portfolio value
    final_value = cash + (shares * df.iloc[-1]['close'])
    total_return = final_value - initial_balance
    return_pct = (total_return / initial_balance) * 100

    # Display results
    print("=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"\nTotal Trades: {len(trades)}")
    print(f"\nTrade History:")
    for trade in trades[:10]:  # Show first 10 trades
        print(f"  {trade['date'].date()} | {trade['action']:4s} | "
              f"{trade['shares']:3d} shares @ ${trade['price']:.2f} | "
              f"Total: ${trade['total']:,.2f}")
    if len(trades) > 10:
        print(f"  ... and {len(trades) - 10} more trades")

    print(f"\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Initial Balance:    ${initial_balance:,.2f}")
    print(f"Final Balance:      ${cash:,.2f}")
    print(f"Shares Held:        {shares}")
    print(f"Shares Value:       ${shares * df.iloc[-1]['close']:,.2f}")
    print(f"Total Portfolio:    ${final_value:,.2f}")
    print(f"Total Return:       ${total_return:+,.2f} ({return_pct:+.2f}%)")
    print("=" * 60)

    # Calculate some metrics
    if len(trades) > 0:
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']

        print(f"\nBuy Trades:  {len(buy_trades)}")
        print(f"Sell Trades: {len(sell_trades)}")

        if len(sell_trades) > 0:
            # Calculate win rate
            winning_trades = 0
            for i, sell in enumerate(sell_trades):
                if i < len(buy_trades):
                    if sell['price'] > buy_trades[i]['price']:
                        winning_trades += 1

            win_rate = (winning_trades / len(sell_trades)) * 100
            print(f"Win Rate:    {win_rate:.1f}%")

    return df, trades, final_value


if __name__ == "__main__":
    try:
        # Run backtest
        symbol = "AAPL"
        df, trades, final_value = backtest_strategy(symbol, initial_balance=100000)

        print("\n✨ Backtest completed!")
        print("\nNote: This is a simple example. Real strategies should include:")
        print("  - Transaction costs")
        print("  - Slippage")
        print("  - Risk management")
        print("  - Multiple indicators")
        print("  - Portfolio diversification")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
