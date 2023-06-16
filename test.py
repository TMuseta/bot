import alpaca_trade_api as tradeapi
from tabulate import tabulate
import time

# Set up Alpaca API credentials
api_key = 'PK02XZUNCN2UTBJM9G2S'
api_secret = 'wghm5IHeKF9GasRCdNEYW9BmorBSZGej9rMHegoh'
base_url = 'https://paper-api.alpaca.markets'
api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')

# Define trading parameters
symbol = 'AAPL'
buy_qty = 10
sell_qty = 10
profit_pct = 0.35
buying_power_limit = 10000  # Set the buying power limit in dollars

# Define buy and sell functions
def buy():
    api.submit_order(
        symbol=symbol,
        qty=buy_qty,
        side='buy',
        type='market',
        time_in_force='gtc'
    )
    print(f'Bought {buy_qty} shares of {symbol} at market price')

def sell():
    api.submit_order(
        symbol=symbol,
        qty=sell_qty,
        side='sell',
        type='market',
        time_in_force='gtc'
    )
    print(f'Sold {sell_qty} shares of {symbol} at market price')

def sell_all():
    positions = api.list_positions()
    for position in positions:
        if position.symbol == symbol:
            sell_qty = int(position.qty)
            current_price = float(api.get_latest_trade(symbol).price)
            unrealized_pl = float(position.unrealized_pl)
            sell_qty = min(sell_qty, sell_qty)  # Adjust the sell quantity based on available quantity
            sell()
            activities.append(['Sell All', symbol, sell_qty, f'${current_price:.2f}', f'${unrealized_pl:.2f}'])

# Define main trading loop
activities = []
bought = False  # Flag to track if stock has been bought
while True:
    # Get current price
    current_price = float(api.get_latest_trade(symbol).price)

    # Check if we need to sell first
    position = api.get_position(symbol)
    if position and not bought:
        sell_qty = int(position.qty)
        sell()
        activities.append(['Sell', symbol, sell_qty, f'${current_price:.2f}', f'${position.unrealized_pl:.2f}'])

    # Check if we need to buy
    cash = float(api.get_account().cash)
    if not bought and cash > current_price * buy_qty and cash > buying_power_limit:
        buy()
        activities.append(['Buy', symbol, buy_qty, f'${current_price:.2f}'])
        bought = True

    # Print account details
    account = api.get_account()
    equity = float(account.equity)
    buying_power = float(account.buying_power)
    buying_power_limit_dollars = float(buying_power_limit)
    print(f'Account Details: Cash: ${float(account.cash):.2f}, Equity: ${equity:.2f}, Buying Power: ${buying_power:.2f}, Buying Power Limit: ${buying_power_limit_dollars:.2f}')

    # Print activities in table format
    print(tabulate(activities, headers=['Action', 'Symbol', 'Quantity', 'Price', 'Profit']))

    # Sell all orders if specified
    sell_all_orders = input("Sell all orders? (y/n): ")
    if sell_all_orders.lower() == 'y':
        sell_all()

    # Wait for 5 seconds before checking again
    time.sleep(5)
