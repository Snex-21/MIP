from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv() 

bot_token = os.getenv("BOT_TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

root_dir = Path(__file__).parent
