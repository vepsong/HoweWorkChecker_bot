import os
import logging
from dotenv import load_dotenv

load_dotenv()
# TELEGRAM_CHAT_ID=2036745661
try:
    PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
except Exception:
    # raise logging.error(f"{Exception} private auth data wasn't found")
    raise