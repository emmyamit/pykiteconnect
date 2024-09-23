import schedule
import time
import subprocess
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

def run_script(script_name):
    """Run a Python script using subprocess."""
    try:
        logging.info(f"Starting {script_name}...")
        result = subprocess.run(['python', script_name], capture_output=True, text=True)
        logging.info(f"{script_name} output:\n{result.stdout}")
        if result.stderr:
            logging.error(f"{script_name} errors:\n{result.stderr}")
    except Exception as e:
        logging.error(f"An error occurred while running {script_name}: {e}")

def job():
    """Run file 1 and file 2 one after the other."""
    run_script('history.py')  # Run file 1
    run_script('orders.py')  # Run file 2
    run_script('history_pe.py')  # Run file 3
    run_script('orders_pe.py')  # Run file 4

# Schedule the job to run every 5 minutes
schedule.every(30).seconds.do(job)

# Keep running the scheduler
if __name__ == "__main__":
    logging.info("Starting the scheduling process.")
    while True:
        schedule.run_pending()
        time.sleep(0)  # Wait for a second before checking the schedule again
