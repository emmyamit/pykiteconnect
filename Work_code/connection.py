import logging
import json
from kiteconnect import KiteConnect

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Step 1: Load API key and secret from key.json
with open('kite_key.json', 'r') as f:
    keys = json.load(f)

api_key = keys.get('api_key')
api_secret = keys.get('api_secret')

# Step 2: Create a KiteConnect session
kite = KiteConnect(api_key=api_key)

# Replace this with your login link and retrieve the request token after login
# https://kite.zerodha.com/connect/login?api_key=your_api_key&v=3
request_token = "S2fxydiSOmao8iRFTVDVq5WhcJib7XVE"  # You need to manually enter this after login

# Step 3: Generate session
data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]
print("Access Token:", access_token)

# Step 4: Save the session (access token) to a file for reuse
session_data = {
    "access_token": access_token
}

with open('kite_session.json', 'w') as f:
    json.dump(session_data, f)

# Set the access token
kite.set_access_token(access_token)
