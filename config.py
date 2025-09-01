import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
    USE_NEW_ORDER_FLOW = False

config = Config()