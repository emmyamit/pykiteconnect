import json
import os
import logging
from datetime import datetime
from kiteconnect import KiteConnect

# Define the symbol for which we want to check and place an order (example: NIFTY)
symbol = 'BANKNIFTY2491151200PE'
quantity = '60'

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Step 1: Load API key and secret from key.json
with open('kite_key.json', 'r') as f:
    keys = json.load(f)

api_key = keys.get('api_key')
api_secret = keys.get('api_secret')

# Step 2: Load the stored session (access token) from the JSON file
with open('kite_session.json', 'r') as f:
    session_data = json.load(f)

access_token = session_data.get("access_token")

# Step 3: Initialize KiteConnect with the saved access token
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

#############################################################################################

# Initialize logging
logging.basicConfig(level=logging.DEBUG)


# 1. Check if there is an existing order in order_pe.json
def check_existing_order(symbol, order_file='order_pe.json'):
    if os.path.exists(order_file):
        with open(order_file, 'r') as file:
            try:
                orders = json.load(file)
            except json.JSONDecodeError:
                orders = []  # If JSON is malformed or empty, treat it as no orders
    else:
        orders = []  # No file means no orders

    for order in orders:
        if order.get('symbol') == symbol:
            return order  # Return the existing order

    return None  # No existing order for the symbol

# 2. Check the signal in signal_pe.json file
def check_signal(signal_file='signal_pe.json'):
    if os.path.exists(signal_file):
        with open(signal_file, 'r') as file:
            try:
                signals = json.load(file)
            except json.JSONDecodeError:
                logging.error("Error reading signal_pe.json")
                return None
    else:
        logging.error(f"{signal_file} not found!")
        return None

    # Retrieve the value of 'Supertrend_Signal' key
    return signals.get("Supertrend_Signal", "")

# 3. Buy stock if signal is "Buy" and no existing order
def buy_stock(symbol, order_file='order_pe.json', signal_file='signal_pe.json'):
    supertrend_signal = check_signal(signal_file)
    existing_order = check_existing_order(symbol, order_file)

    if supertrend_signal == "Buy":
        if not existing_order:
            logging.info(f"Placing buy order for {symbol}.")
            place_new_order(symbol, order_type="Buy", order_file=order_file)
##########################################################################################################
            # Place an order
            try:
                order_id = kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    exchange=kite.EXCHANGE_NSE,
                    tradingsymbol=symbol,
                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                    quantity=quantity,
                    product=kite.PRODUCT_CNC,
                    order_type=kite.ORDER_TYPE_MARKET
                )
            
                logging.info("Order placed. ID is: {}".format(order_id))
            except Exception as e:
                logging.info("Order placement failed: {}".format(e))
###########################################################################################################                
        else:
            logging.info(f"Buy order for {symbol} already exists. Waiting for sell signal.")
    else:
        logging.info(f"No buy signal found for {symbol}.")

# 4. Update the order in order_pe.json
def update_order(symbol, new_order_type, order_file='order_pe.json'):
    if os.path.exists(order_file):
        with open(order_file, 'r') as file:
            try:
                orders = json.load(file)
            except json.JSONDecodeError:
                orders = []
    else:
        orders = []

    order_updated = False
    for order in orders:
        if order['symbol'] == symbol:
            order['order_type'] = new_order_type
            order['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            order_updated = True

    if not order_updated:
        logging.error(f"No existing order found for {symbol} to update.")
        return

    if new_order_type == "Sell":
        # Clear the order_pe.json file if the new order type is "Sell"
        with open(order_file, 'w') as file:
            json.dump([], file)  # Write an empty list to clear the file
        logging.info(f"Order file cleared after selling {symbol}.")
   # else:
   #     with open(order_file, 'w') as file:
   #         json.dump(orders, file, indent=4)
   #     logging.info(f"Order updated to {new_order_type} for {symbol}.")

# Function to place a new order and write it to order_pe.json
def place_new_order(symbol, order_type="Buy", quantity=quantity, order_file='order_pe.json'):
    new_order = {
        "symbol": symbol,
        "order_type": order_type,
        "quantity": quantity,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if os.path.exists(order_file):
        with open(order_file, 'r') as file:
            try:
                orders = json.load(file)
            except json.JSONDecodeError:
                orders = []
    else:
        orders = []

    orders.append(new_order)

    with open(order_file, 'w') as file:
        json.dump(orders, file, indent=4)

    logging.info(f"New order placed: {new_order}")

# 5. Main function to call all functions
def main():
    logging.info("Starting the order management process.")

    # Check the signal and existing orders
    supertrend_signal = check_signal()
    existing_order = check_existing_order(symbol)

    if supertrend_signal == "Buy":
        buy_stock(symbol)
    elif supertrend_signal == "Sell":
        if existing_order and existing_order['order_type'] == 'Buy':
            logging.info(f"Supertrend signal is Sell for {symbol}. Closing buy order.")
            update_order(symbol, "Sell")
        elif not existing_order:
            logging.info(f"No existing order to sell for {symbol}.")
    else:
        logging.info(f"No actionable signal for {symbol}: {supertrend_signal}")

if __name__ == "__main__":
    main()