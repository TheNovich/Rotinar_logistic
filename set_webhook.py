import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://rotinatbot.ddns.net/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Установка webhook через API Telegram
response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    data={
        "url": WEBHOOK_URL,
        "secret_token": WEBHOOK_SECRET
    }
)

print(response.json())