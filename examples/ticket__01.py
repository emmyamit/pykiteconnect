###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Zerodha Technology Pvt. Ltd.
#
# This example shows how to subscribe and get ticks from Kite Connect ticker,
# For more info read documentation - https://kite.trade/docs/connect/v1/#streaming-websocket
###############################################################################

import logging
from kiteconnect import KiteTicker
import threading
import time
import keyboard

logging.basicConfig(level=logging.DEBUG)    

# Initialise
kws = KiteTicker("luu5ax574l5l4wy5", "gyPyBcX8UyDcmSmaXx6IYLjK3LbptMQf")

# def on_ticks(ws, ticks):  # noqa
#     # Callback to receive ticks.
#     logging.info("Ticks: {}".format(ticks))

# def on_connect(ws, response):  # noqa
#     # Callback on successful connect.
#     # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
#     ws.subscribe([738561, 5633])

#     # Set RELIANCE to tick in `full` mode.
#     ws.set_mode(ws.MODE_FULL, [738561])

# def on_order_update(ws, data):
#     logging.debug("Order update : {}".format(data))

# # Assign the callbacks.
# kws.on_ticks = on_ticks
# kws.on_connect = on_connect
# kws.on_order_update = on_order_update

# # Infinite loop on the main thread. Nothing after this will run.
# # You have to use the pre-defined callbacks to manage subscriptions.
# kws.connect()


def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.info("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (replace with actual tokens).
    ws.subscribe([738561])  # Replace with your instrument tokens
    # Set mode for full tick data
    ws.set_mode(ws.MODE_FULL, [738561])  # Replace with your instrument tokens

def on_order_update(ws, data):
    logging.debug("Order update : {}".format(data))

def on_close(ws, code, reason):
    # On connection close, log the reason
    logging.error(f"Connection closed with code {code} and reason {reason}")
    # Exit the script
    exit()

def monitor_keyboard(event, hotkey='q'):
    while not event.is_set():
        if keyboard.is_pressed(hotkey):  # Check if the specified hotkey is pressed
            logging.info(f"Hotkey '{hotkey}' pressed, closing connection...")
            kws.close()  # Close the WebSocket connection
            event.set()  # Signal to stop monitoring
        time.sleep(0.1)  # Check every 100ms

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_order_update = on_order_update
kws.on_close = on_close  # Assign on_close callback

# Create an event to manage graceful shutdown
shutdown_event = threading.Event()

# Start the WebSocket connection
kws.connect(threaded=True)

# Start the keyboard monitoring thread
keyboard_thread = threading.Thread(target=monitor_keyboard, args=(shutdown_event,), daemon=True)
keyboard_thread.start()

# Wait for the keyboard thread to signal shutdown
shutdown_event.wait()