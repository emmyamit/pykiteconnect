import json
import os
import logging
from datetime import datetime
from kiteconnect import KiteConnect
import pandas as pd

# Define the symbol for which we want to check and place an order (example: NIFTY)
csv_file_path = 'options_tradingsymbols_pe.csv'  # Update this with the actual path to your file
options_csv_df = pd.read_csv(csv_file_path)
symbol = options_csv_df.tradingsymbol.iloc[0]

# Quantity to buy or sell
quantity = 1

# Configure logging to output to log.txt with timestamp
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
                logging.error(f"Error reading {signal_file}. Invalid JSON format.")
                return None, None
    else:
        logging.error(f"{signal_file} not found!")
        return None, None

    # Retrieve the 'Supertrend_Signal' and 'close' values
    supertrend_signal = signals.get("Supertrend_Signal", "")
    close_price = signals.get("close", "")
    
    return supertrend_signal, close_price

##########################################################################################################


# Fetch the average price for a specific order using its order_id
def get_order_average_price(order_id):
    try:
        # Fetch the specific order details using the order_id
        order_history = kite.order_history(order_id)
        
        if order_history:
            # The last order update contains the final average price
            latest_order = order_history[-1]  # The last entry is the most recent update
            avg_price = latest_order.get('average_price', None)

            if avg_price is not None:
                logging.info(f"Average price for order {order_id}: {avg_price}")
                return avg_price
            else:
                logging.warning(f"No average price available for order {order_id}")
                return None
        else:
            logging.warning(f"No order history available for order {order_id}")
            return None
    except Exception as e:
        logging.error(f"Error fetching order history for {order_id}: {e}")
        return None

# Write the average price to a JSON file
def write_avg_price_to_json(order_id, avg_price, filename="avg_price.json"):
    data = {"order_id": order_id, "average_price": avg_price}
    try:
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        logging.info(f"Average price for order {order_id} written to {filename}")
    except Exception as e:
        logging.error(f"Error writing to {filename}: {e}")


##########################################################################################################

# 3. Manage buy and sell orders in one function
def manage_order(symbol, quantity, order_file='order_pe.json', signal_file='signal_pe.json'):
    supertrend_signal, close_price = check_signal(signal_file)
    existing_order = check_existing_order(symbol, order_file)

    if supertrend_signal == "Buy":
        if not existing_order or existing_order['order_type'] == "Sell":
            logging.info(f"Placing buy order for {symbol}.")
            place_new_order(symbol, order_type="Buy", quantity=quantity, order_file=order_file)

            # Place a buy order
            try:
                order_id = kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    exchange=kite.EXCHANGE_NSE,
                    tradingsymbol=symbol,
                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                    quantity=quantity,
                    product=kite.PRODUCT_NRML,
                    order_type=kite.ORDER_TYPE_MARKET
                )
                # Example usage
                avg_price = get_order_average_price(order_id)
                # If average price is retrieved, write it to avg_price.json
                if avg_price:
                    write_avg_price_to_json(order_id, avg_price)
                else:
                   logging.info(f"Failed to retrieve average price for order {order_id}")
                logging.info(f"Buy order placed for {symbol}, Order ID: {order_id}")
            except Exception as e:
               logging.error(f"Buy order placement failed: {e}")     
        else:
            logging.info(f"Buy order for {symbol} already exists. Waiting for sell signal.")
                            
    if supertrend_signal == "Sell" or close_price >= avg_price + 20:
        if not existing_order or existing_order['order_type'] == "Buy":
            logging.info(f"Placing sell order for {symbol}.")
            order_id = place_new_order(symbol, order_type="Sell", quantity=quantity, order_file=order_file)

            # Place a sell order
            try:
                kite.place_order(
                    variety=kite.VARIETY_REGULAR,
                    exchange=kite.EXCHANGE_NSE,
                    tradingsymbol=symbol,
                    transaction_type=kite.TRANSACTION_TYPE_SELL,
                    quantity=quantity,
                    product=kite.PRODUCT_NRML,
                    order_type=kite.ORDER_TYPE_MARKET
                )
                logging.info(f"Sell order placed for {symbol}.")
            except Exception as e:
                logging.error(f"Sell order placement failed: {e}")
        else:
            logging.info(f"Sell order for {symbol} already exists. Waiting for new buy signal.")

    else:
        logging.info(f"No actionable signal for {symbol}: {supertrend_signal}")

###########################################################################################################

# Function to place a new order and write it to order_pe.json (clears old orders)
def place_new_order(symbol, order_type="Buy", quantity=quantity, order_file='order_pe.json'):
    new_order = {
        "symbol": symbol,
        "order_type": order_type,
        "quantity": quantity,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Clear the old orders by overwriting the file with the new order only
    with open(order_file, 'w') as file:
        json.dump([new_order], file, indent=4)  # Write only the new order, overwriting the old one

    logging.info(f"New {order_type} order placed: {new_order}")
    return new_order.get('order_id')  # Return the order ID to append to avg_price.json

###########################################################################################################

# Function to append order ID to avg_price.json
def append_order_id_to_json(order_id, avg_price_file='avg_price.json'):
    data = {}
    
    # Load existing data if file exists
    if os.path.exists(avg_price_file):
        with open(avg_price_file, 'r') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                logging.error(f"Error reading {avg_price_file}. Invalid JSON format.")
    
    # Append the new order ID
    data['order_id'] = order_id

    # Write updated data back to the file
    with open(avg_price_file, 'w') as file:
        json.dump(data, file, indent=4)
    
    logging.info(f"Appended order ID {order_id} to {avg_price_file}")

###########################################################################################################

# 4. Main function to call the order management function
def main():
    logging.info("Starting the order management process.")
    # Manage both buy and sell orders based on the signal
    manage_order(symbol, quantity)

if __name__ == "__main__":
    main()