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
kws = KiteTicker("luu5ax574l5l4wy5", "l1Qgq4T5w7T1iw7C630TSZwbEGyyq6aZ")

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.info("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    logging.info("Connected: {}".format(response))
    # Subscribe to a list of instrument_tokens (replace with actual tokens).
    ws.subscribe([256265])  # Replace with your instrument tokens
    # Set mode for full tick data
    ws.set_mode(ws.MODE_FULL, [256265])  # Replace with your instrument tokens

def on_order_update(ws, data):
    logging.debug("Order update : {}".format(data))

def on_close(ws, code, reason):
    # On connection close, log the reason
    logging.error(f"Connection closed with code {code} and reason {reason}")

def monitor_keyboard(event, hotkey='q'):
    while not event.is_set():
        if keyboard.is_pressed(hotkey):  # Check if the specified hotkey is pressed
            logging.info(f"Hotkey '{hotkey}' pressed, closing connection...")
            kws.close()  # Close the WebSocket connection
            event.set()  # Signal to stop monitoring
        time.sleep(0.1)  # Check every 100ms

def main():
    # Assign the callbacks.
    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_order_update = on_order_update
    kws.on_close = on_close  # Assign on_close callback

    # Create an event to manage graceful shutdown
    shutdown_event = threading.Event()

    # Start the WebSocket connection
    kws.connect(threaded=True)

    # Start the keyboard monitoring thread with 'q' as the hotkey
    keyboard_thread = threading.Thread(target=monitor_keyboard, args=(shutdown_event, 'q'), daemon=True)
    keyboard_thread.start()

    # Wait for the keyboard thread to signal shutdown
    shutdown_event.wait()

    # Ensure WebSocket connection is closed before exiting
    kws.close()

if __name__ == "__main__":
    main()