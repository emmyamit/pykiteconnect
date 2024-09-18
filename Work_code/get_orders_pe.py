import logging
from kiteconnect import KiteConnect
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import talib
import json

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

################################################################################################

# # # Fetch the order history using KiteConnect API
# try:
#     orders = kite.orders()  # Fetch all orders
#     if orders:
#         order_df = pd.DataFrame(orders)  # Convert to DataFrame for easier manipulation
#         logging.info(f"Order history fetched successfully. Total orders: {len(orders)}")

#         # Save order history to a CSV file
#         # order_df.to_csv('order_history.csv', index=False)
#         # logging.info("Order history saved to order_history.csv")

#     else:
#         logging.info("No order history available.")
# except Exception as e:
#     logging.error(f"Error fetching order history: {e}")


###################################################################################################


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

# Example usage
order_id_to_check = '240918800232476'  # Replace with the actual order_id you want to check
avg_price = get_order_average_price(order_id_to_check)

# If average price is retrieved, write it to avg_price.json
if avg_price:
    write_avg_price_to_json(order_id_to_check, avg_price)
else:
    logging.info(f"Failed to retrieve average price for order {order_id_to_check}")