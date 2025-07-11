# logger_util.py
import logging
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

LOG_ENDPOINT = os.getenv("LOG_ENDPOINT")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Optional: also log to file
logging.basicConfig(
    filename="access.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def Log(source: str, level: str, layer: str, message: str):
    log_text = f"[{source.upper()}] [{layer.upper()}] {message}"
    
    # 1. Local log (optional)
    if level == "info":
        logging.info(log_text)
    elif level == "error":
        logging.error(log_text)
    elif level == "fatal":
        logging.critical(log_text)
    else:
        logging.warning(log_text)

    # 2. Remote log API
    payload = {
        "source": source,
        "level": level,
        "layer": layer,
        "message": message
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(LOG_ENDPOINT, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"[LOGGER ERROR] Could not send log: {e}")
