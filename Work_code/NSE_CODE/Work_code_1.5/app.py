import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import subprocess
import logging
import os
import signal
import json

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Load credentials from JSON file
def load_credentials():
    with open('credentials.json', 'r') as f:
        return json.load(f)

credentials = load_credentials()

# Initialize the Dash app
app = dash.Dash(__name__)

# Keep track of the process and login status
process = None
logged_in = False

# Layout of the Dash app
app.layout = html.Div([
    html.H1("Control Main.py from Dash UI"),
    dcc.Input(id='username-input', type='text', placeholder='Username'),
    dcc.Input(id='password-input', type='password', placeholder='Password'),
    html.Button("Login", id="login-button", n_clicks=0),
    html.Div(id="login-status", style={"margin-top": "20px"}),  # To display login status
    html.Div(id="script-controls", style={"margin-top": "20px", "display": "none"}, children=[
        html.Button("Start Script", id="start-script-button", n_clicks=0, style={"margin-right": "10px"}),
        html.Button("Stop Script", id="stop-script-button", n_clicks=0),
        html.Div(id="output-status", style={"margin-top": "20px"})  # To display status
    ])
])

# Callback to handle login
@app.callback(
    [Output("login-status", "children"),
     Output("script-controls", "style")],
    Input("login-button", "n_clicks"),
    [Input("username-input", "value"),
     Input("password-input", "value")]
)
def login(n_clicks, username, password):
    global logged_in
    if n_clicks > 0:
        if username == credentials["username"] and password == credentials["password"]:
            logged_in = True
            return "Login successful!", {"display": "block"}
        else:
            return "Invalid username or password.", {"display": "none"}
    return "", {"display": "none"}

# Callback to handle start and stop buttons
@app.callback(
    Output("output-status", "children"),
    [Input("start-script-button", "n_clicks"),
     Input("stop-script-button", "n_clicks")]
)
def control_main_script(start_clicks, stop_clicks):
    global process

    # If start button is clicked
    if start_clicks > 0 and (not process or process.poll() is not None):
        try:
            logging.info("Starting main.py script...")
            process = subprocess.Popen(['python', 'main.py'])
            return "main.py script has been started!"
        except Exception as e:
            logging.error(f"Failed to start main.py: {e}")
            return f"Error: {e}"

    # If stop button is clicked
    if stop_clicks > 0 and process and process.poll() is None:
        try:
            logging.info("Stopping main.py script...")
            process.terminate()  # Gracefully terminate the process
            process.wait()       # Ensure the process has stopped
            return "main.py script has been stopped!"
        except Exception as e:
            logging.error(f"Failed to stop main.py: {e}")
            return f"Error: {e}"

    return "Click a button to start or stop main.py"

# Run the Dash app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=1994, debug=True)
