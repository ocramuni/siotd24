import configparser
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env
TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")

def read_config(section, key):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config[section][key]

async def send_message(application, message):
    await application.bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                                       text=message)