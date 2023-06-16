import alpaca_trade_api as tradeapi
from datetime import datetime, time
import pandas as pd
import time
from tabulate import tabulate

# Alpaca API credentials
ALPACA_API_KEY = 'AK52BG2PJZIKP3AZHFCJ'
ALPACA_SECRET_KEY = 'DrP5tL91qQrBjSuSfrG8NW8quJLF5nw4zT1hNPbn'
BASE_URL = 'https://api.alpaca.markets'  # Paper trading URL, change to 'https://api.alpaca.markets' for live trading

# Trading parameters
SYMBOL = 'CVNA'  # Stock symbol to trade
QUANTITY = 10  # Number of shares to trade
STOP_LOSS = 1.25  # Stop loss percentage (1.25 = 25% stop loss)
TAKE_PROFIT = 7 / QUANTITY  # Take profit amount per stock
LIMIT_ORDER_OFFSET = 0.05  # Offset for the limit order price from the current price

# Initialize Alpaca API
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=BASE_URL, api_version='v2')

# Function to get the account's available cash
def get_available_cash():
    account = api.get_account()
    return float(account.cash)

# Function to check if the market is open (including extended hours)
def is_market_open():
    clock = api.get_clock()
    return clock.is_open

# Function to place a market order
def place_market_order(side, qty):
    try:
        api.submit_order(
            symbol=SYMBOL,
            qty=qty,
            side=side,
            type='market',
            time_in_force='gtc'
        )
        return True
    except Exception as e:
        print(f"Error placing market order: {e}")
        return False

# Function to place a limit order
def place_limit_order(side, qty, price):
    try:
        api.submit_order(
            symbol=SYMBOL,
            qty=qty,
            side=side,
            type='limit',
            time_in_force='gtc',
            limit_price=price
        )
        return True
    except Exception as e:
        print(f"Error placing limit order: {e}")
        return False

# Function to get the current price of the stock
def get_current_price():
    try:
        barset = api.get_bars(SYMBOL, '1Min', limit=1)
        price = barset[0].c
        return float(price)
    except Exception as e:
        print(f"Error getting current price: {e}")
        return None

# Function to print account details in a fancy table format
def print_account_details(account):
    account_data = [
        ['Cash', '${:,.2f}'.format(float(account.cash))],
        ['Portfolio Value', '${:,.2f}'.format(float(account.portfolio_value))],
        ['Buying Power', '${:,.2f}'.format(float(account.buying_power))],
        ['Equity', '${:,.2f}'.format(float(account.equity))]
    ]
    print(tabulate(account_data, headers=['Account Details', 'Amount'], tablefmt='fancy_grid'))

# Function to calculate the profit from buy and sell orders
def calculate_profit(buy_orders, sell_orders):
    buy_price = sum([float(order['Price']) for order in buy_orders])
    sell_price = sum([float(order['Price']) for order in sell_orders])
    profit = sell_price - buy_price
    return profit

# Function to print trading activities in a table format
def print_trading_activities(activities):
    df = pd.DataFrame([a._raw for a in activities])
    print(df.to_string(index=False))

# Main trading logic
def run_trading_bot():
    buy_order_placed = False
    buy_orders = []
    sell_orders = []

    while True:
        if is_market_open() or api.get_clock().is_open == 'extended':
            if not buy_order_placed:
                current_price = get_current_price()
                if current_price is not None:
                    available_cash = get_available_cash()
                    if available_cash > 0:
                        open_orders = api.list_orders(status='open')
                        cvna_orders = [order for order in open_orders if order.symbol == SYMBOL]
                        if len(cvna_orders) == 0:
                            if current_price < (1 - STOP_LOSS) * get_current_price():
                                # Place a market sell order at the stop loss percentage
                                place_market_order('sell', QUANTITY)
                                print(f"Stop loss triggered. Selling {QUANTITY} shares at market price.")
                                sell_orders.append({
                                    'Type': 'Sell',
                                    'Qty': QUANTITY,
                                    'Price': current_price
                                })
                                buy_order_placed = False
                            elif current_price > (1 + TAKE_PROFIT) * get_current_price():
                                # Place a market sell order at the take profit amount per stock
                                take_profit_price = round(current_price + TAKE_PROFIT, 2)
                                place_limit_order('sell', QUANTITY, take_profit_price)
                                print(f"Take profit triggered. Selling {QUANTITY} shares at ${take_profit_price}.")
                                sell_orders.append({
                                    'Type': 'Sell',
                                    'Qty': QUANTITY,
                                    'Price': take_profit_price
                                })
                                buy_order_placed = False
                            else:
                                # Place a limit buy order at a price slightly below the current price
                                buy_price = round(current_price * (1 - LIMIT_ORDER_OFFSET), 2)
                                place_limit_order('buy', QUANTITY, buy_price)
                                print(f"Placed limit buy order for {QUANTITY} shares at ${buy_price}.")
                                buy_orders.append({
                                    'Type': 'Buy',
                                    'Qty': QUANTITY,
                                    'Price': buy_price
                                })
                                buy_order_placed = True
                        else:
                            print("There is an open order for CVNA. Waiting for it to be executed...")
                    else:
                        print("Insufficient available cash.")
            else:
                # Check if a sell order has been executed
                orders = api.list_orders(status='filled')
                if orders:
                    for order in orders:
                        if order.side == 'sell' and order.symbol == SYMBOL:
                            sell_orders.append({
                                'Type': 'Sell',
                                'Qty': order.qty,
                                'Price': order.filled_avg_price
                            })
                            buy_order_placed = False
                            break
                else:
                    print("Sell order is still open. Waiting for it to be executed...")
        else:
            print("Market is closed. Placing a limit order...")
            current_price = get_current_price()
            if current_price is not None:
                # Place a limit buy order at the current price
                buy_price = round(current_price, 2)  # Round to nearest penny
                place_limit_order('buy', QUANTITY, buy_price)
                print(f"Placed limit buy order for {QUANTITY} shares at ${buy_price}.")
                buy_orders.append({
                    'Type': 'Buy',
                    'Qty': QUANTITY,
                    'Price': buy_price
                })
                buy_order_placed = True

        # Print account details
        account = api.get_account()
        print("Account Details:")
        print_account_details(account)

        # Print trading activities
        activities = api.get_activities()
        print("Trading Activities:")
        print_trading_activities(activities)

        # Calculate profit
        profit = calculate_profit(buy_orders, sell_orders)

        # Print order details and profit
        order_details = buy_orders + sell_orders
        print("Order Details:")
        print(tabulate(order_details, headers='keys', tablefmt='fancy_grid'))
        print(f"Profit: ${profit:,.2f}")

        time.sleep(60)  # Sleep for 1 minute and check again

# Start the trading bot
if __name__ == '__main__':
    run_trading_bot()
